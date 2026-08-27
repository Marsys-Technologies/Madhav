// @vitest-environment node
import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import { Pool } from 'pg'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { runNirmanaEvidenceOwnershipPreflight } from '../../scripts/nirmana-evidence-ownership-preflight'
import { applyNirmanaEvidenceOwnershipMarker } from '../../scripts/nirmana-evidence-ownership-marker'

const url = process.env.NIRMANA_EVIDENCE_PREFLIGHT_TEST_DATABASE_URL
let admin: Pool

describe.skipIf(!url)('Nirmana direct-owner preflight — disposable PostgreSQL', () => {
  beforeAll(async () => {
    admin = new Pool({ connectionString: url })
    await admin.query(`CREATE ROLE amjis_app LOGIN CREATEROLE CREATEDB; GRANT CONNECT ON DATABASE nirmana_evidence_preflight_test TO amjis_app; ALTER DATABASE nirmana_evidence_preflight_test OWNER TO amjis_app; ALTER SCHEMA public OWNER TO amjis_app; CREATE TABLE _migrations_applied (filename text PRIMARY KEY, sha256 text NOT NULL); ALTER TABLE _migrations_applied OWNER TO amjis_app;`)
    await admin.query(`SET ROLE amjis_app; ${readFileSync(resolve(__dirname, '../../migrations/592_nirmana_elevation_campaign_evidence.sql'), 'utf8')}`)
    await admin.query(`SET ROLE amjis_app; ${readFileSync(resolve(__dirname, '../../migrations/627_nirmana_elevation_asset_labels.sql'), 'utf8')}`)
    await admin.query(`SET ROLE amjis_app; CREATE TABLE asset_registry (asset_id text); CREATE TABLE nirmana_elevation_monitor_observations (id text); CREATE TABLE build_runs (id text); CREATE TABLE build_run_assets (id text); CREATE TABLE asset_provenance_receipts (id text); CREATE TABLE asset_output_digest_specs (id text); CREATE ROLE nirmana_evidence_ingress_writer LOGIN NOINHERIT; CREATE ROLE nirmana_migrator LOGIN NOINHERIT;`)
    await admin.query(`SET ROLE amjis_app; ${readFileSync(resolve(__dirname, '../../migrations/632_nirmana_evidence_server_writer_guard.sql'), 'utf8')}; INSERT INTO _migrations_applied (filename, sha256) VALUES ('632_nirmana_evidence_server_writer_guard.sql', repeat('0', 64)); RESET ROLE`)
  })
  afterAll(async () => { await admin?.end() })
  it('refuses arbitrary pre-existing evidence-owner membership', async () => {
    await admin.query(`CREATE ROLE nirmana_evidence_owner NOLOGIN; CREATE ROLE unrelated_member LOGIN; GRANT nirmana_evidence_owner TO unrelated_member`)
    const legacy = new URL(url!)
    legacy.username = 'amjis_app'
    await expect(runNirmanaEvidenceOwnershipPreflight(legacy.toString())).rejects.toThrow(/pre-existing memberships/i)
    await admin.query('REVOKE nirmana_evidence_owner FROM unrelated_member; DROP ROLE unrelated_member; DROP ROLE nirmana_evidence_owner')
  })

  it('refuses a principal that can assume the ingress writer before any handoff mutation', async () => {
    await admin.query('CREATE ROLE ingress_assumer LOGIN; GRANT nirmana_evidence_ingress_writer TO ingress_assumer')
    const legacy = new URL(url!)
    legacy.username = 'amjis_app'
    await expect(runNirmanaEvidenceOwnershipPreflight(legacy.toString())).rejects.toThrow(/ingress writer with memberships/i)
    await admin.query('REVOKE nirmana_evidence_ingress_writer FROM ingress_assumer; DROP ROLE ingress_assumer')
  })

  it('rolls back a forced preflight failure and leaves no owner membership', async () => {
    await admin.query('DROP TABLE asset_provenance_receipts')
    const legacy = new URL(url!)
    legacy.username = 'amjis_app'
    await expect(runNirmanaEvidenceOwnershipPreflight(legacy.toString())).rejects.toThrow()
    const memberships = await admin.query(`SELECT count(*)::text AS count FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.roleid OR r.oid=m.member WHERE r.rolname='nirmana_evidence_owner'`)
    expect(memberships.rows[0]?.count).toBe('0')
    await admin.query('SET ROLE amjis_app; CREATE TABLE asset_provenance_receipts (id text); RESET ROLE')
  })

  it('fails closed on an interrupted partial handoff rather than reacquiring ownership', async () => {
    await admin.query('CREATE ROLE nirmana_evidence_owner NOLOGIN NOINHERIT; CREATE SCHEMA nirmana_evidence AUTHORIZATION nirmana_evidence_owner')
    const legacy = new URL(url!)
    legacy.username = 'amjis_app'
    await expect(runNirmanaEvidenceOwnershipPreflight(legacy.toString())).rejects.toThrow(/partial handoff/i)
    await admin.query('DROP SCHEMA nirmana_evidence; DROP ROLE nirmana_evidence_owner')
  })

  it('moves campaign objects into an owned schema and denies generic destructive DDL', async () => {
    const legacy = new URL(url!)
    legacy.username = 'amjis_app'
    await expect(runNirmanaEvidenceOwnershipPreflight(legacy.toString())).resolves.toBeUndefined()
    // Simulates an interruption after the handoff commit but before marker 633:
    // replay must validate state and return without trying to reclaim ownership.
    await expect(runNirmanaEvidenceOwnershipPreflight(legacy.toString())).resolves.toBeUndefined()
    const generic = new Pool({ connectionString: legacy.toString() })
    await expect(generic.query('DROP SCHEMA nirmana_evidence CASCADE')).rejects.toThrow(/must be owner|permission denied/i)
    await expect(generic.query('CREATE TABLE nirmana_evidence.generic_escape (id text)')).rejects.toThrow(/permission denied/i)
    await expect(generic.query(`INSERT INTO nirmana_evidence.nirmana_elevation_campaign_definitions
      (campaign_id, definition_revision, definition_status, manifest, manifest_sha256, created_by)
      VALUES ('nirmana-elevation', 'generic', 'reconciling', '{}'::jsonb, repeat('a', 64), 'generic')`)).rejects.toThrow(/permission denied/i)
    await generic.end()

    const controlUrl = new URL(url!)
    controlUrl.username = 'nirmana_campaign_control_writer'
    const control = new Pool({ connectionString: controlUrl.toString() })
    await Promise.all([
      'asset_registry', 'nirmana_elevation_monitor_observations', 'build_runs',
      'build_run_assets', 'asset_provenance_receipts', 'asset_output_digest_specs',
      '_migrations_applied',
    ].map((relation) => expect(control.query(`SELECT * FROM public.${relation}`)).resolves.toBeDefined()))
    await admin.query('SET ROLE amjis_app; CREATE TABLE public.control_writer_forbidden (id text); RESET ROLE')
    await expect(control.query('SELECT * FROM public.control_writer_forbidden')).rejects.toThrow(/permission denied/i)
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

    const ingressUrl = new URL(url!)
    ingressUrl.username = 'nirmana_evidence_ingress_writer'
    const ingress = new Pool({ connectionString: ingressUrl.toString() })
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
    const migratorUrl = new URL(url!)
    migratorUrl.username = 'nirmana_migrator'
    const migrator = new Pool({ connectionString: migratorUrl.toString() })
    const markerSql = readFileSync(resolve(__dirname, '../../migrations/633_nirmana_evidence_writer_ownership.sql'), 'utf8')
    await admin.query('CREATE ROLE migrator_escape LOGIN; GRANT nirmana_migrator TO migrator_escape')
    await expect(migrator.query(markerSql)).rejects.toThrow(/protected writer role memberships/i)
    await admin.query('REVOKE nirmana_migrator FROM migrator_escape; DROP ROLE migrator_escape')
    await migrator.end()
    const legacy = new URL(url!)
    legacy.username = 'amjis_app'
    await expect(applyNirmanaEvidenceOwnershipMarker(migratorUrl.toString())).resolves.toBeUndefined()
    await expect(runNirmanaEvidenceOwnershipPreflight(legacy.toString())).resolves.toBeUndefined()
  })
})
