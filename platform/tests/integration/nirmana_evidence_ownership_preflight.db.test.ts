// @vitest-environment node
import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import { Pool } from 'pg'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { runNirmanaEvidenceOwnershipPreflight } from '../../scripts/nirmana-evidence-ownership-preflight'
import { applyNirmanaEvidenceOwnershipMarker } from '../../scripts/nirmana-evidence-ownership-marker'
import { readNirmanaEvidenceOwnershipStatus, requiresNirmanaEvidenceLegacyOwner } from '../../scripts/nirmana-evidence-ownership-status'

const url = process.env.NIRMANA_EVIDENCE_PREFLIGHT_TEST_DATABASE_URL
const roleAuthToken = ['nirmana', 'preflight', 'fixture', 'auth'].join('-')
const originalControlUrl = process.env.NIRMANA_CAMPAIGN_CONTROL_DATABASE_URL
let admin: Pool

function roleUrl(role: string): string {
  const roleUrl = new URL(url!)
  roleUrl.username = role
  roleUrl.password = roleAuthToken
  return roleUrl.toString()
}

describe.skipIf(!url)('Nirmana direct-owner preflight — disposable PostgreSQL', () => {
  beforeAll(async () => {
    admin = new Pool({ connectionString: url })
    await admin.query(`CREATE ROLE amjis_app LOGIN PASSWORD '${roleAuthToken}' CREATEROLE CREATEDB; GRANT CONNECT ON DATABASE nirmana_evidence_preflight_test TO amjis_app; ALTER DATABASE nirmana_evidence_preflight_test OWNER TO amjis_app; ALTER SCHEMA public OWNER TO amjis_app; CREATE TABLE _migrations_applied (filename text PRIMARY KEY, sha256 text NOT NULL); ALTER TABLE _migrations_applied OWNER TO amjis_app;`)
    await admin.query(`SET ROLE amjis_app; ${readFileSync(resolve(__dirname, '../../migrations/592_nirmana_elevation_campaign_evidence.sql'), 'utf8')}`)
    await admin.query(`SET ROLE amjis_app; ${readFileSync(resolve(__dirname, '../../migrations/627_nirmana_elevation_asset_labels.sql'), 'utf8')}`)
    await admin.query(`SET ROLE amjis_app; CREATE TABLE asset_registry (asset_id text); CREATE TABLE nirmana_elevation_monitor_observations (id text); CREATE TABLE build_runs (id text); CREATE TABLE build_run_assets (id text); CREATE TABLE asset_provenance_receipts (id text); CREATE TABLE asset_output_digest_specs (id text); CREATE ROLE nirmana_evidence_ingress_writer LOGIN PASSWORD '${roleAuthToken}' NOINHERIT; CREATE ROLE nirmana_migrator LOGIN PASSWORD '${roleAuthToken}' NOINHERIT; CREATE ROLE nirmana_campaign_control_writer LOGIN PASSWORD '${roleAuthToken}' NOINHERIT;`)
    await admin.query(`SET ROLE amjis_app; ${readFileSync(resolve(__dirname, '../../migrations/632_nirmana_evidence_server_writer_guard.sql'), 'utf8')}; INSERT INTO _migrations_applied (filename, sha256) VALUES ('632_nirmana_evidence_server_writer_guard.sql', repeat('0', 64)); RESET ROLE`)
    await admin.query(`SET ROLE amjis_app;
      CREATE TABLE public.control_acl_stale (id text);
      CREATE SEQUENCE public.control_acl_stale_seq;
      GRANT ALL PRIVILEGES ON TABLE public.control_acl_stale TO nirmana_campaign_control_writer, nirmana_migrator;
      GRANT ALL PRIVILEGES ON SEQUENCE public.control_acl_stale_seq TO nirmana_campaign_control_writer, nirmana_migrator;
      GRANT SELECT (asset_id) ON TABLE public.asset_registry TO nirmana_campaign_control_writer, nirmana_migrator;
      RESET ROLE`)
    process.env.NIRMANA_CAMPAIGN_CONTROL_DATABASE_URL = roleUrl('nirmana_campaign_control_writer')
  })
  afterAll(async () => {
    if (originalControlUrl === undefined) delete process.env.NIRMANA_CAMPAIGN_CONTROL_DATABASE_URL
    else process.env.NIRMANA_CAMPAIGN_CONTROL_DATABASE_URL = originalControlUrl
    await admin?.end()
  })
  it('refuses arbitrary pre-existing evidence-owner membership', async () => {
    await admin.query(`CREATE ROLE nirmana_evidence_owner NOLOGIN; CREATE ROLE unrelated_member LOGIN; GRANT nirmana_evidence_owner TO unrelated_member`)
    await expect(runNirmanaEvidenceOwnershipPreflight(roleUrl('amjis_app'))).rejects.toThrow(/pre-existing memberships/i)
    await admin.query('REVOKE nirmana_evidence_owner FROM unrelated_member; DROP ROLE unrelated_member; DROP ROLE nirmana_evidence_owner')
  })

  it('refuses a principal that can assume the ingress writer before any handoff mutation', async () => {
    await admin.query('CREATE ROLE ingress_assumer LOGIN; GRANT nirmana_evidence_ingress_writer TO ingress_assumer')
    await expect(runNirmanaEvidenceOwnershipPreflight(roleUrl('amjis_app'))).rejects.toThrow(/ingress writer with memberships/i)
    await admin.query('REVOKE nirmana_evidence_ingress_writer FROM ingress_assumer; DROP ROLE ingress_assumer')
  })

  it('requires a successfully authenticated preprovisioned control writer before handoff', async () => {
    const configured = process.env.NIRMANA_CAMPAIGN_CONTROL_DATABASE_URL
    delete process.env.NIRMANA_CAMPAIGN_CONTROL_DATABASE_URL
    await expect(runNirmanaEvidenceOwnershipPreflight(roleUrl('amjis_app'))).rejects.toThrow(/control writer must be secret-backed/i)
    process.env.NIRMANA_CAMPAIGN_CONTROL_DATABASE_URL = configured
  })

  it('fails closed when the generic marker probe cannot read its ledger', async () => {
    await admin.query(`CREATE ROLE marker_reader_denied LOGIN PASSWORD '${roleAuthToken}'; GRANT CONNECT ON DATABASE nirmana_evidence_preflight_test TO marker_reader_denied; GRANT USAGE ON SCHEMA public TO marker_reader_denied`)
    await expect(readNirmanaEvidenceOwnershipStatus(roleUrl('marker_reader_denied'))).rejects.toThrow(/permission denied/i)
    await admin.query('DROP OWNED BY marker_reader_denied; DROP ROLE marker_reader_denied')
  })

  it('uses the generic marker principal only for a read-only ledger probe', async () => {
    await admin.query(`SET ROLE amjis_app;
      CREATE ROLE marker_reader LOGIN PASSWORD '${roleAuthToken}';
      GRANT CONNECT ON DATABASE nirmana_evidence_preflight_test TO marker_reader;
      GRANT USAGE ON SCHEMA public TO marker_reader;
      GRANT SELECT ON public._migrations_applied TO marker_reader;
      RESET ROLE`)
    await expect(readNirmanaEvidenceOwnershipStatus(roleUrl('marker_reader'))).resolves.toBe('unmarked')
    const reader = new Pool({ connectionString: roleUrl('marker_reader') })
    await expect(reader.query(`INSERT INTO public._migrations_applied (filename, sha256)
      VALUES ('forbidden-marker-write.sql', repeat('0', 64))`)).rejects.toThrow(/permission denied/i)
    await reader.end()
    await admin.query('DROP OWNED BY marker_reader; DROP ROLE marker_reader')
  })

  it('fails closed on a third-party default ACL that could grant a protected writer future access', async () => {
    await admin.query(`CREATE ROLE hostile_default_grantor NOLOGIN;
      GRANT CREATE ON SCHEMA public TO hostile_default_grantor;
      ALTER DEFAULT PRIVILEGES FOR ROLE hostile_default_grantor IN SCHEMA public
        GRANT SELECT ON TABLES TO PUBLIC`)
    await expect(runNirmanaEvidenceOwnershipPreflight(roleUrl('amjis_app')))
      .rejects.toThrow(/protected-writer default ACLs/i)
    await admin.query(`ALTER DEFAULT PRIVILEGES FOR ROLE hostile_default_grantor IN SCHEMA public
      REVOKE ALL PRIVILEGES ON TABLES FROM PUBLIC;
      REVOKE CREATE ON SCHEMA public FROM hostile_default_grantor;
      DROP ROLE hostile_default_grantor`)
  })

  it('fails closed on a relevant third-party grantor with no override row for hard-wired function and type defaults', async () => {
    await admin.query(`CREATE ROLE hardwired_default_grantor NOLOGIN;
      GRANT CREATE ON SCHEMA public TO hardwired_default_grantor`)
    await expect(runNirmanaEvidenceOwnershipPreflight(roleUrl('amjis_app')))
      .rejects.toThrow(/hard-wired PUBLIC function\/type defaults/i)
    await admin.query('REVOKE CREATE ON SCHEMA public FROM hardwired_default_grantor; DROP ROLE hardwired_default_grantor')
  })

  it('rolls back a forced preflight failure and leaves no owner membership', async () => {
    await admin.query('DROP TABLE asset_provenance_receipts')
    await expect(runNirmanaEvidenceOwnershipPreflight(roleUrl('amjis_app'))).rejects.toThrow()
    const memberships = await admin.query(`SELECT count(*)::text AS count FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.roleid OR r.oid=m.member WHERE r.rolname='nirmana_evidence_owner'`)
    expect(memberships.rows[0]?.count).toBe('0')
    await admin.query('SET ROLE amjis_app; CREATE TABLE asset_provenance_receipts (id text); RESET ROLE')
  })

  it('fails closed on an interrupted partial handoff rather than reacquiring ownership', async () => {
    await admin.query('CREATE ROLE nirmana_evidence_owner NOLOGIN NOINHERIT; CREATE SCHEMA nirmana_evidence AUTHORIZATION nirmana_evidence_owner')
    await expect(runNirmanaEvidenceOwnershipPreflight(roleUrl('amjis_app'))).rejects.toThrow(/partial handoff/i)
    await admin.query('DROP SCHEMA nirmana_evidence; DROP ROLE nirmana_evidence_owner')
  })

  it('moves campaign objects into an owned schema and denies generic destructive DDL', async () => {
    const legacy = roleUrl('amjis_app')
    await admin.query(`SET ROLE amjis_app;
      ALTER DEFAULT PRIVILEGES FOR ROLE amjis_app IN SCHEMA public
        GRANT SELECT, REFERENCES, TRIGGER ON TABLES TO PUBLIC, nirmana_campaign_control_writer, nirmana_migrator;
      RESET ROLE`)
    await expect(runNirmanaEvidenceOwnershipPreflight(legacy)).resolves.toBeUndefined()
    // Simulates an interruption after the handoff commit but before marker 633:
    // replay must validate state and return without trying to reclaim ownership.
    await expect(runNirmanaEvidenceOwnershipPreflight(legacy)).resolves.toBeUndefined()
    const generic = new Pool({ connectionString: legacy })
    await expect(generic.query('DROP SCHEMA nirmana_evidence CASCADE')).rejects.toThrow(/must be owner|permission denied/i)
    await expect(generic.query('CREATE TABLE nirmana_evidence.generic_escape (id text)')).rejects.toThrow(/permission denied/i)
    await expect(generic.query(`INSERT INTO nirmana_evidence.nirmana_elevation_campaign_definitions
      (campaign_id, definition_revision, definition_status, manifest, manifest_sha256, created_by)
      VALUES ('nirmana-elevation', 'generic', 'reconciling', '{}'::jsonb, repeat('a', 64), 'generic')`)).rejects.toThrow(/permission denied/i)
    await generic.end()

    const control = new Pool({ connectionString: roleUrl('nirmana_campaign_control_writer') })
    await Promise.all([
      'asset_registry', 'nirmana_elevation_monitor_observations', 'build_runs',
      'build_run_assets', 'asset_provenance_receipts',
      '_migrations_applied',
    ].map((relation) => expect(control.query(`SELECT * FROM public.${relation}`)).resolves.toBeDefined()))
    await admin.query('SET ROLE amjis_app; CREATE TABLE public.control_writer_forbidden (id text); RESET ROLE')
    await expect(control.query('SELECT * FROM public.control_writer_forbidden')).rejects.toThrow(/permission denied/i)
    await expect(control.query('SELECT * FROM public.control_acl_stale')).rejects.toThrow(/permission denied/i)
    await expect(control.query('SELECT * FROM public.asset_output_digest_specs')).rejects.toThrow(/permission denied/i)
    await control.query(`INSERT INTO nirmana_evidence.nirmana_elevation_campaign_definitions
      (campaign_id, definition_revision, definition_status, manifest, manifest_sha256, created_by)
      VALUES ('nirmana-elevation', 'control-r1', 'reconciling', '{}'::jsonb, repeat('a', 64), 'control')`)
    await control.query(`INSERT INTO nirmana_evidence.nirmana_elevation_campaign_events
      (campaign_id, definition_revision, idempotency_key, event_type, entity_type, entity_id,
       evidence_payload, source_kind, source_ref, observed_at, recorded_by)
      VALUES ('nirmana-elevation', 'control-r1', 'control-event', 'asset_analysis_accepted', 'asset', 'bg_reference',
       '{}'::jsonb, 'operator', 'control-test', now(), 'control')`)
    await expect(control.query(`INSERT INTO nirmana_evidence.nirmana_elevation_campaign_events
      (campaign_id, definition_revision, idempotency_key, event_type, entity_type, entity_id,
       evidence_payload, source_kind, source_ref, observed_at, recorded_by)
      VALUES ('nirmana-elevation', 'control-server', 'server', 'asset_analysis_accepted', 'asset', 'bg_reference',
       '{}'::jsonb, 'server_reconstructed', 'control-test', now(), 'control')`)).rejects.toThrow(/ingress writer/i)
    await control.end()

    const ingress = new Pool({ connectionString: roleUrl('nirmana_evidence_ingress_writer') })
    await ingress.query(`INSERT INTO nirmana_evidence.nirmana_elevation_campaign_events
      (campaign_id, definition_revision, idempotency_key, event_type, entity_type, entity_id,
       evidence_payload, source_kind, source_ref, observed_at, recorded_by)
      VALUES ('nirmana-elevation', 'control-r1', 'ingress-event', 'probe_accepted', 'asset', 'bg_reference',
       '{}'::jsonb, 'server_reconstructed', 'runner', now(), 'ingress')`)
    await expect(ingress.query(`INSERT INTO nirmana_evidence.nirmana_elevation_campaign_events
      (campaign_id, definition_revision, idempotency_key, event_type, entity_type, entity_id,
       evidence_payload, source_kind, source_ref, observed_at, recorded_by)
      VALUES ('nirmana-elevation', 'ingress-control', 'control', 'asset_analysis_accepted', 'asset', 'bg_reference',
       '{}'::jsonb, 'operator', 'ingress', now(), 'ingress')`)).rejects.toThrow(/control writer/i)
    await ingress.end()

    const identities = await admin.query<{ writer_identity: string }>(`SELECT writer_identity FROM nirmana_evidence.nirmana_elevation_campaign_events ORDER BY idempotency_key`)
    expect(identities.rows.map((row) => row.writer_identity).sort()).toEqual([
      'nirmana_campaign_control_writer',
      'nirmana_evidence_ingress_writer',
    ])
    const roleState = await admin.query<{ rolcreatedb: boolean; rolcreaterole: boolean }>(`SELECT rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname = 'amjis_app'`)
    expect(roleState.rows[0]).toEqual({ rolcreatedb: false, rolcreaterole: false })
    const ownership = await admin.query<{ owner: string }>(`SELECT owner.rolname AS owner FROM pg_namespace namespace JOIN pg_roles owner ON owner.oid = namespace.nspowner WHERE namespace.nspname = 'nirmana_evidence'`)
    expect(ownership.rows[0]?.owner).toBe('nirmana_evidence_owner')
    const sharedSchema = await admin.query<{ owner_create: boolean; ingress_create: boolean; control_create: boolean; migrator_create: boolean }>(`
      SELECT has_schema_privilege('nirmana_evidence_owner', 'public', 'CREATE') AS owner_create,
             has_schema_privilege('nirmana_evidence_ingress_writer', 'public', 'CREATE') AS ingress_create,
             has_schema_privilege('nirmana_campaign_control_writer', 'public', 'CREATE') AS control_create,
             has_schema_privilege('nirmana_migrator', 'public', 'CREATE') AS migrator_create
    `)
    expect(sharedSchema.rows[0]).toEqual({ owner_create: false, ingress_create: false, control_create: false, migrator_create: false })
    await admin.query('SET ROLE amjis_app; CREATE TABLE public.default_acl_after_handoff (id text); RESET ROLE')
    const futurePublicAcl = await admin.query<{ control_read: boolean; control_references: boolean; control_trigger: boolean; migrator_read: boolean }>(`
      SELECT has_table_privilege('nirmana_campaign_control_writer', 'public.default_acl_after_handoff', 'SELECT') AS control_read,
             has_table_privilege('nirmana_campaign_control_writer', 'public.default_acl_after_handoff', 'REFERENCES') AS control_references,
             has_table_privilege('nirmana_campaign_control_writer', 'public.default_acl_after_handoff', 'TRIGGER') AS control_trigger,
             has_table_privilege('nirmana_migrator', 'public.default_acl_after_handoff', 'SELECT') AS migrator_read
    `)
    expect(futurePublicAcl.rows[0]).toEqual({ control_read: false, control_references: false, control_trigger: false, migrator_read: false })
    const staleAcl = await admin.query<{ control_table: boolean; migrator_table: boolean; control_sequence: boolean; migrator_sequence: boolean; control_column_clean: boolean; migrator_column_clean: boolean }>(`
      SELECT has_table_privilege('nirmana_campaign_control_writer', 'public.control_acl_stale', 'SELECT') AS control_table,
             has_table_privilege('nirmana_migrator', 'public.control_acl_stale', 'SELECT') AS migrator_table,
             has_sequence_privilege('nirmana_campaign_control_writer', 'public.control_acl_stale_seq', 'USAGE') AS control_sequence,
             has_sequence_privilege('nirmana_migrator', 'public.control_acl_stale_seq', 'USAGE') AS migrator_sequence,
             NOT EXISTS (SELECT 1 FROM pg_attribute attribute JOIN pg_class relation ON relation.oid = attribute.attrelid JOIN pg_namespace namespace ON namespace.oid = relation.relnamespace CROSS JOIN LATERAL aclexplode(attribute.attacl) AS column_acl JOIN pg_roles grantee ON grantee.oid = column_acl.grantee WHERE namespace.nspname = 'public' AND relation.relname = 'asset_registry' AND attribute.attname = 'asset_id' AND grantee.rolname = 'nirmana_campaign_control_writer') AS control_column_clean,
             NOT EXISTS (SELECT 1 FROM pg_attribute attribute JOIN pg_class relation ON relation.oid = attribute.attrelid JOIN pg_namespace namespace ON namespace.oid = relation.relnamespace CROSS JOIN LATERAL aclexplode(attribute.attacl) AS column_acl JOIN pg_roles grantee ON grantee.oid = column_acl.grantee WHERE namespace.nspname = 'public' AND relation.relname = 'asset_registry' AND attribute.attname = 'asset_id' AND grantee.rolname = 'nirmana_migrator') AS migrator_column_clean
    `)
    expect(staleAcl.rows[0]).toEqual({ control_table: false, migrator_table: false, control_sequence: false, migrator_sequence: false, control_column_clean: true, migrator_column_clean: true })
    const membershipEnvelope = await admin.query<{ roleid: string; member: string }>(`
      SELECT parent.rolname AS roleid, member.rolname AS member
        FROM pg_auth_members membership
        JOIN pg_roles parent ON parent.oid = membership.roleid
        JOIN pg_roles member ON member.oid = membership.member
       WHERE parent.rolname = ANY (ARRAY['nirmana_evidence_owner', 'nirmana_evidence_ingress_writer', 'nirmana_campaign_control_writer', 'nirmana_migrator'])
          OR member.rolname = ANY (ARRAY['nirmana_evidence_owner', 'nirmana_evidence_ingress_writer', 'nirmana_campaign_control_writer', 'nirmana_migrator'])
    `)
    expect(membershipEnvelope.rows).toEqual([])
  })

  it('permits the dedicated migrator to attest, record the marker, and makes preflight replay a no-op', async () => {
    const migratorUrl = roleUrl('nirmana_migrator')
    const migrator = new Pool({ connectionString: migratorUrl })
    const markerSql = readFileSync(resolve(__dirname, '../../migrations/633_nirmana_evidence_writer_ownership.sql'), 'utf8')
    await admin.query('CREATE ROLE migrator_escape LOGIN; GRANT nirmana_migrator TO migrator_escape')
    await expect(migrator.query(markerSql)).rejects.toThrow(/protected writer role memberships/i)
    await admin.query('REVOKE nirmana_migrator FROM migrator_escape; DROP ROLE migrator_escape')
    await migrator.end()
    const beforeMarker = await readNirmanaEvidenceOwnershipStatus(url)
    expect(beforeMarker).toBe('unmarked')
    expect(requiresNirmanaEvidenceLegacyOwner(beforeMarker)).toBe(true)
    await admin.query('SET ROLE amjis_app; GRANT REFERENCES (asset_id) ON public.asset_registry TO PUBLIC; RESET ROLE')
    await expect(applyNirmanaEvidenceOwnershipMarker(migratorUrl))
      .rejects.toThrow(/non-owner writer ACLs outside the explicit envelope/i)
    await admin.query('SET ROLE amjis_app; REVOKE REFERENCES (asset_id) ON public.asset_registry FROM PUBLIC; RESET ROLE')
    await expect(applyNirmanaEvidenceOwnershipMarker(migratorUrl)).resolves.toBeUndefined()
    const afterMarker = await readNirmanaEvidenceOwnershipStatus(url)
    expect(afterMarker).toBe('marked')
    expect(requiresNirmanaEvidenceLegacyOwner(afterMarker)).toBe(false)
    await admin.query('SET ROLE amjis_app; CREATE TABLE public.default_acl_after_marker (id text); RESET ROLE')
    const postMarkerAcl = await admin.query<{ control_read: boolean; migrator_read: boolean }>(`
      SELECT has_table_privilege('nirmana_campaign_control_writer', 'public.default_acl_after_marker', 'SELECT') AS control_read,
             has_table_privilege('nirmana_migrator', 'public.default_acl_after_marker', 'SELECT') AS migrator_read
    `)
    expect(postMarkerAcl.rows[0]).toEqual({ control_read: false, migrator_read: false })
    await admin.query(`SET ROLE amjis_app;
      CREATE FUNCTION public.default_acl_after_marker_security_definer() RETURNS text
        LANGUAGE sql SECURITY DEFINER AS 'SELECT ''safe''::text';
      CREATE TYPE public.default_acl_after_marker_type AS ENUM ('safe');
      RESET ROLE`)
    const postMarkerRoutineAcl = await admin.query<{
      owner_execute: boolean; ingress_execute: boolean; control_execute: boolean; migrator_execute: boolean
      owner_type_usage: boolean; ingress_type_usage: boolean; control_type_usage: boolean; migrator_type_usage: boolean
    }>(`
      SELECT has_function_privilege('nirmana_evidence_owner', 'public.default_acl_after_marker_security_definer()'::regprocedure, 'EXECUTE') AS owner_execute,
             has_function_privilege('nirmana_evidence_ingress_writer', 'public.default_acl_after_marker_security_definer()'::regprocedure, 'EXECUTE') AS ingress_execute,
             has_function_privilege('nirmana_campaign_control_writer', 'public.default_acl_after_marker_security_definer()'::regprocedure, 'EXECUTE') AS control_execute,
             has_function_privilege('nirmana_migrator', 'public.default_acl_after_marker_security_definer()'::regprocedure, 'EXECUTE') AS migrator_execute,
             has_type_privilege('nirmana_evidence_owner', 'public.default_acl_after_marker_type'::regtype, 'USAGE') AS owner_type_usage,
             has_type_privilege('nirmana_evidence_ingress_writer', 'public.default_acl_after_marker_type'::regtype, 'USAGE') AS ingress_type_usage,
             has_type_privilege('nirmana_campaign_control_writer', 'public.default_acl_after_marker_type'::regtype, 'USAGE') AS control_type_usage,
             has_type_privilege('nirmana_migrator', 'public.default_acl_after_marker_type'::regtype, 'USAGE') AS migrator_type_usage
    `)
    expect(postMarkerRoutineAcl.rows[0]).toEqual({
      owner_execute: false, ingress_execute: false, control_execute: false, migrator_execute: false,
      owner_type_usage: false, ingress_type_usage: false, control_type_usage: false, migrator_type_usage: false,
    })
    await expect(runNirmanaEvidenceOwnershipPreflight(roleUrl('amjis_app'))).resolves.toBeUndefined()
  })
})
