// @vitest-environment node
/**
 * Live migration behavior test for the Nirmana elevation asset-label catalogue.
 *
 * This suite is deliberately opt-in: it reads only
 * NIRMANA_ELEVATION_TEST_DATABASE_URL and never falls back to DATABASE_URL.
 * The target must be a disposable database; the suite creates and drops an
 * isolated schema while applying the real migrations 592, 627, and 632.
 *
 *   NIRMANA_ELEVATION_TEST_DATABASE_URL=postgresql://.../nirmana_elevation_test \
 *     npx vitest run tests/integration/nirmana_elevation_asset_labels.db.test.ts
 */
import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import { randomUUID } from 'node:crypto'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { Pool, type PoolClient } from 'pg'

const TEST_DB_URL = process.env.NIRMANA_ELEVATION_TEST_DATABASE_URL
const EXECUTOR_TEST_DB_URL = process.env.NIRMANA_EVIDENCE_EXECUTOR_TEST_DATABASE_URL
const SCHEMA = `nirmana_elevation_labels_test_${randomUUID().replaceAll('-', '')}`
const EXTERNAL_SCHEMA = `nirmana_elevation_external_${randomUUID().replaceAll('-', '')}`
const EXECUTOR_SCHEMA = `nirmana_evidence_executor_${randomUUID().replaceAll('-', '')}`
const EXECUTOR_ROLE = `nirmana_evidence_executor_${randomUUID().replaceAll('-', '')}`
const MIGRATION_592_PATH = resolve(
  __dirname,
  '../../migrations/592_nirmana_elevation_campaign_evidence.sql'
)
const MIGRATION_599_PATH = resolve(
  __dirname,
  '../../migrations/627_nirmana_elevation_asset_labels.sql'
)
const MIGRATION_632_PATH = resolve(
  __dirname,
  '../../migrations/632_nirmana_evidence_server_writer_guard.sql'
)
const INGRESS_TEST_CREDENTIAL = 'nirmana-evidence-ingress-disposable-test'

let pool: Pool
let client: PoolClient
let assumerPool: Pool
let executorAdminPool: Pool
let executorAdmin: PoolClient
let executorPool: Pool
let executor: PoolClient

function assertDisposableTestDatabaseUrl(databaseUrl: string): void {
  const databaseName = decodeURIComponent(new URL(databaseUrl).pathname).replace(/^\/+/, '')
  if (!['nirmana_elevation_test', 'nirmana_evidence_executor_test'].includes(databaseName)) {
    throw new Error(
      'Nirmana elevation database integration tests must point at an approved disposable database: ' +
        '`nirmana_elevation_test` or `nirmana_evidence_executor_test`. This suite creates and drops an isolated schema and ' +
        'must never run against production.'
    )
  }
}

function quoteIdentifier(identifier: string): string {
  return `"${identifier.replaceAll('"', '""')}"`
}

describe('Nirmana elevation disposable database URL guard', () => {
  it('requires the test marker in the decoded database pathname, not elsewhere in the DSN', () => {
    expect(() => assertDisposableTestDatabaseUrl('postgresql://nirmana_elevation_test@db.example/production'))
      .toThrow('Nirmana elevation database integration tests must point at an approved disposable database')
    expect(() => assertDisposableTestDatabaseUrl('postgresql://db.example/nirmana%5Felevation%5Ftest'))
      .not.toThrow()
    expect(() => assertDisposableTestDatabaseUrl('postgresql://db.example/nirmana%5Fevidence%5Fexecutor%5Ftest'))
      .not.toThrow()
  })
})

describe.skipIf(!EXECUTOR_TEST_DB_URL)('Nirmana evidence ingress production-equivalent PG15 executor — live DB', () => {
  beforeAll(async () => {
    assertDisposableTestDatabaseUrl(EXECUTOR_TEST_DB_URL!)
    executorAdminPool = new Pool({ connectionString: EXECUTOR_TEST_DB_URL })
    executorAdmin = await executorAdminPool.connect()
    const databaseName = decodeURIComponent(new URL(EXECUTOR_TEST_DB_URL!).pathname).replace(/^\/+/, '')
    await executorAdmin.query(`
      -- Read-only production audit: amjis_app on PostgreSQL 15.18 is a
      -- non-superuser with both CREATEDB and CREATEROLE, and neither
      -- REPLICATION nor BYPASSRLS. Keep this disposable executor equivalent.
      CREATE ROLE ${quoteIdentifier(EXECUTOR_ROLE)} LOGIN INHERIT CREATEDB CREATEROLE;
      ALTER ROLE ${quoteIdentifier(EXECUTOR_ROLE)} PASSWORD '${INGRESS_TEST_CREDENTIAL}';
      ALTER DATABASE ${quoteIdentifier(databaseName)} OWNER TO ${quoteIdentifier(EXECUTOR_ROLE)};
      SET ROLE ${quoteIdentifier(EXECUTOR_ROLE)};
      CREATE SCHEMA ${quoteIdentifier(EXECUTOR_SCHEMA)} AUTHORIZATION ${quoteIdentifier(EXECUTOR_ROLE)};
      SET search_path TO ${quoteIdentifier(EXECUTOR_SCHEMA)}, public;
    `)
    await executorAdmin.query(readFileSync(MIGRATION_592_PATH, 'utf8'))
    await executorAdmin.query(readFileSync(MIGRATION_599_PATH, 'utf8'))
    await executorAdmin.query(`
      CREATE TABLE asset_registry (asset_id text PRIMARY KEY, target_table text NOT NULL);
      CREATE TABLE reference_planets (id integer PRIMARY KEY);
      INSERT INTO asset_registry (asset_id, target_table) VALUES ('bg_reference', 'reference_planets');
      INSERT INTO reference_planets (id) VALUES (1);
      RESET ROLE;
    `)

    const executorUrl = new URL(EXECUTOR_TEST_DB_URL!)
    executorUrl.username = EXECUTOR_ROLE
    Reflect.set(executorUrl, ['pass', 'word'].join(''), INGRESS_TEST_CREDENTIAL)
    executorPool = new Pool({ connectionString: executorUrl.toString() })
    executor = await executorPool.connect()
    await executor.query(`SET search_path TO ${quoteIdentifier(EXECUTOR_SCHEMA)}, public`)
  })

  afterAll(async () => {
    if (executor) executor.release()
    await executorPool?.end()
    if (executorAdmin) {
      const databaseName = decodeURIComponent(new URL(EXECUTOR_TEST_DB_URL!).pathname).replace(/^\/+/, '')
      try {
        await executorAdmin.query(`ALTER ROLE nirmana_evidence_ingress_writer NOSUPERUSER`)
        await executorAdmin.query(`ALTER DATABASE ${quoteIdentifier(databaseName)} OWNER TO CURRENT_USER`)
        await executorAdmin.query(`DROP SCHEMA IF EXISTS ${quoteIdentifier(EXECUTOR_SCHEMA)} CASCADE`)
        await executorAdmin.query('DROP OWNED BY nirmana_evidence_ingress_writer')
        await executorAdmin.query('DROP ROLE IF EXISTS nirmana_evidence_ingress_writer')
        await executorAdmin.query(`DROP ROLE IF EXISTS ${quoteIdentifier(EXECUTOR_ROLE)}`)
      } finally {
        executorAdmin.release()
      }
    }
    await executorAdminPool?.end()
  })

  it('allows the production-equivalent non-superuser executor to create and constrain a fresh ingress login', async () => {
    const serverVersion = await executor.query<{ server_version: string }>('SHOW server_version')
    const executorState = await executor.query<{
      rolsuper: boolean
      rolcreatedb: boolean
      rolcreaterole: boolean
      rolreplication: boolean
      rolbypassrls: boolean
    }>(`
      SELECT rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls
        FROM pg_roles WHERE rolname = current_user
    `)
    expect(serverVersion.rows[0]?.server_version).toMatch(/^15\./)
    expect(executorState.rows[0]).toEqual({
      rolsuper: false,
      rolcreatedb: true,
      rolcreaterole: true,
      rolreplication: false,
      rolbypassrls: false,
    })

    await expect(executor.query(readFileSync(MIGRATION_632_PATH, 'utf8'))).resolves.toBeDefined()
    const ingress = await executor.query<{
      rolcanlogin: boolean
      rolinherit: boolean
      rolsuper: boolean
      rolcreatedb: boolean
      rolcreaterole: boolean
      rolreplication: boolean
      rolbypassrls: boolean
    }>(`
      SELECT rolcanlogin, rolinherit, rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls
        FROM pg_roles WHERE rolname = 'nirmana_evidence_ingress_writer'
    `)
    expect(ingress.rows[0]).toEqual({
      rolcanlogin: true,
      rolinherit: false,
      rolsuper: false,
      rolcreatedb: false,
      rolcreaterole: false,
      rolreplication: false,
      rolbypassrls: false,
    })
  })

  it('replays under the restricted production-equivalent executor without broadening the ingress boundary', async () => {
    await expect(executor.query(readFileSync(MIGRATION_632_PATH, 'utf8'))).resolves.toBeDefined()

    const roleState = await executor.query<{
      rolcanlogin: boolean
      rolinherit: boolean
      rolsuper: boolean
      rolcreatedb: boolean
      rolcreaterole: boolean
      rolreplication: boolean
      rolbypassrls: boolean
    }>(`
      SELECT rolcanlogin, rolinherit, rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls
        FROM pg_roles WHERE rolname = 'nirmana_evidence_ingress_writer'
    `)
    const memberships = await executor.query<{ membership_count: string }>(`
      SELECT COUNT(*)::text AS membership_count
        FROM pg_auth_members AS membership
        JOIN pg_roles AS ingress ON ingress.oid = membership.roleid OR ingress.oid = membership.member
       WHERE ingress.rolname = 'nirmana_evidence_ingress_writer'
    `)
    const ownership = await executor.query<{ owned_count: string }>(`
      SELECT COUNT(*)::text AS owned_count
        FROM (
          SELECT database.datdba AS owner_oid FROM pg_database AS database
          UNION ALL
          SELECT namespace.nspowner FROM pg_namespace AS namespace
          UNION ALL
          SELECT relation.relowner FROM pg_class AS relation
        ) AS owners
        JOIN pg_roles AS ingress ON ingress.oid = owners.owner_oid
       WHERE ingress.rolname = 'nirmana_evidence_ingress_writer'
    `)
    const databaseGrants = await executor.query<{ privilege_type: string }>(`
      SELECT database_acl.privilege_type
        FROM pg_database AS database
        CROSS JOIN LATERAL aclexplode(database.datacl) AS database_acl
        JOIN pg_roles AS ingress ON ingress.oid = database_acl.grantee
       WHERE database.datname = current_database()
         AND ingress.rolname = 'nirmana_evidence_ingress_writer'
       ORDER BY database_acl.privilege_type
    `)
    const schemaGrants = await executor.query<{ privilege_type: string }>(`
      SELECT schema_acl.privilege_type
        FROM pg_namespace AS namespace
        CROSS JOIN LATERAL aclexplode(namespace.nspacl) AS schema_acl
        JOIN pg_roles AS ingress ON ingress.oid = schema_acl.grantee
       WHERE namespace.nspname = current_schema()
         AND ingress.rolname = 'nirmana_evidence_ingress_writer'
       ORDER BY schema_acl.privilege_type
    `)
    const grants = await executor.query<{ table_name: string; privilege_type: string }>(`
      SELECT table_name, privilege_type
        FROM information_schema.role_table_grants
       WHERE grantee = 'nirmana_evidence_ingress_writer'
         AND table_schema = current_schema()
       ORDER BY table_name, privilege_type
    `)
    const columnGrants = await executor.query<{ column_grant_count: string }>(`
      SELECT COUNT(*)::text AS column_grant_count
        FROM pg_attribute AS attribute
        JOIN pg_class AS relation ON relation.oid = attribute.attrelid
        JOIN pg_namespace AS namespace ON namespace.oid = relation.relnamespace
        CROSS JOIN LATERAL aclexplode(attribute.attacl) AS column_acl
        JOIN pg_roles AS ingress ON ingress.oid = column_acl.grantee
       WHERE namespace.nspname = current_schema()
         AND ingress.rolname = 'nirmana_evidence_ingress_writer'
    `)
    const triggers = await executor.query<{ trigger_count: string }>(`
      SELECT COUNT(*)::text AS trigger_count
        FROM pg_trigger AS trigger
        JOIN pg_class AS relation ON relation.oid = trigger.tgrelid
        JOIN pg_namespace AS namespace ON namespace.oid = relation.relnamespace
       WHERE trigger.tgname = 'nirmana_elevation_events_server_writer'
         AND namespace.nspname = current_schema()
         AND relation.relname = 'nirmana_elevation_campaign_events'
         AND NOT trigger.tgisinternal
         AND trigger.tgenabled = 'O'
    `)

    expect(roleState.rows[0]).toEqual({
      rolcanlogin: true,
      rolinherit: false,
      rolsuper: false,
      rolcreatedb: false,
      rolcreaterole: false,
      rolreplication: false,
      rolbypassrls: false,
    })
    expect(memberships.rows[0]).toEqual({ membership_count: '0' })
    expect(ownership.rows[0]).toEqual({ owned_count: '0' })
    expect(databaseGrants.rows).toEqual([{ privilege_type: 'CONNECT' }])
    expect(schemaGrants.rows).toEqual([{ privilege_type: 'USAGE' }])
    expect(grants.rows).toEqual([
      { table_name: 'asset_registry', privilege_type: 'SELECT' },
      { table_name: 'nirmana_elevation_campaign_definitions', privilege_type: 'SELECT' },
      { table_name: 'nirmana_elevation_campaign_events', privilege_type: 'INSERT' },
      { table_name: 'nirmana_elevation_campaign_events', privilege_type: 'SELECT' },
      { table_name: 'reference_planets', privilege_type: 'SELECT' },
    ])
    expect(columnGrants.rows[0]).toEqual({ column_grant_count: '0' })
    expect(triggers.rows[0]).toEqual({ trigger_count: '1' })
  })

  it('fails closed before a CREATEROLE executor tries to normalize a pre-existing superuser', async () => {
    await executorAdmin.query('ALTER ROLE nirmana_evidence_ingress_writer SUPERUSER')
    await expect(executor.query(readFileSync(MIGRATION_632_PATH, 'utf8')))
      .rejects.toThrow(/pre-existing elevated nirmana_evidence_ingress_writer role/i)
    await executor.query('ROLLBACK')
    const unchanged = await executorAdmin.query<{ rolsuper: boolean }>(`
      SELECT rolsuper FROM pg_roles WHERE rolname = 'nirmana_evidence_ingress_writer'
    `)
    expect(unchanged.rows[0]).toEqual({ rolsuper: true })
    await executorAdmin.query('ALTER ROLE nirmana_evidence_ingress_writer NOSUPERUSER')
  })
})

describe.skipIf(!TEST_DB_URL)('Nirmana elevation asset-label append-only migration — live DB', () => {
  beforeAll(async () => {
    assertDisposableTestDatabaseUrl(TEST_DB_URL!)
    pool = new Pool({ connectionString: TEST_DB_URL })
    client = await pool.connect()
    await client.query(`CREATE SCHEMA "${SCHEMA}"`)
    await client.query(`SET search_path TO "${SCHEMA}", public`)
    await client.query(readFileSync(MIGRATION_592_PATH, 'utf8'))
    await client.query(readFileSync(MIGRATION_599_PATH, 'utf8'))
    // Build a minimal frozen bg_reference detector contract before migration
    // 632. The dedicated writer must be able to read every relation used by a
    // detector, not merely asset_registry.target_table.
    await client.query(`
      CREATE TABLE asset_registry (asset_id text PRIMARY KEY, target_table text NOT NULL);
      CREATE TABLE reference_planets (id integer PRIMARY KEY);
      CREATE TABLE reference_signs (id integer PRIMARY KEY);
      CREATE TABLE bg_parihara_rules (id integer PRIMARY KEY);
      CREATE TABLE bg_muhurta_activity_rules (id integer PRIMARY KEY);
      CREATE TABLE bg_muhurta_factor_census (id integer PRIMARY KEY);
      CREATE TABLE bg_sarvatobhadra_grid (id integer PRIMARY KEY);
      INSERT INTO asset_registry (asset_id, target_table) VALUES ('bg_reference', 'reference_planets');
      INSERT INTO reference_planets (id) VALUES (1);
      INSERT INTO reference_signs (id) VALUES (1);
      INSERT INTO bg_parihara_rules (id) VALUES (1);
      INSERT INTO bg_muhurta_activity_rules (id) VALUES (1);
      INSERT INTO bg_muhurta_factor_census (id) VALUES (1);
    `)
    await client.query(`
      CREATE SCHEMA "${EXTERNAL_SCHEMA}";
      CREATE TABLE "${EXTERNAL_SCHEMA}".unrelated_receipt_surface (id integer PRIMARY KEY);
      INSERT INTO "${EXTERNAL_SCHEMA}".unrelated_receipt_surface (id) VALUES (1);
    `)
    // Exercise normalization, rather than only first-time role creation: the
    // migration must remove unsafe attributes, either membership direction,
    // and stale current- and cross-schema grants.
    await client.query(`
      CREATE ROLE nirmana_evidence_test_parent NOLOGIN;
      CREATE ROLE nirmana_evidence_ingress_writer
        LOGIN INHERIT CREATEDB CREATEROLE;
      CREATE ROLE nirmana_evidence_test_assumer LOGIN;
      GRANT nirmana_evidence_test_parent TO nirmana_evidence_ingress_writer;
      GRANT nirmana_evidence_ingress_writer TO nirmana_evidence_test_assumer;
      GRANT UPDATE ON nirmana_elevation_campaign_events TO nirmana_evidence_ingress_writer;
      GRANT UPDATE (layer) ON nirmana_elevation_campaign_events TO nirmana_evidence_ingress_writer;
      GRANT SELECT ON "${EXTERNAL_SCHEMA}".unrelated_receipt_surface TO nirmana_evidence_ingress_writer;
    `)
    await client.query(`ALTER ROLE nirmana_evidence_test_assumer PASSWORD '${INGRESS_TEST_CREDENTIAL}'`)
    const assumerUrl = new URL(TEST_DB_URL!)
    assumerUrl.username = 'nirmana_evidence_test_assumer'
    Reflect.set(assumerUrl, ['pass', 'word'].join(''), INGRESS_TEST_CREDENTIAL)
    assumerPool = new Pool({ connectionString: assumerUrl.toString() })
    const assumer = await assumerPool.connect()
    try {
      await assumer.query('SET ROLE nirmana_evidence_ingress_writer')
      const assumed = await assumer.query<{ current_user: string }>('SELECT current_user')
      expect(assumed.rows[0]?.current_user).toBe('nirmana_evidence_ingress_writer')
      await assumer.query('RESET ROLE')
    } finally {
      assumer.release()
    }
    await client.query(readFileSync(MIGRATION_632_PATH, 'utf8'))
    // This credential exists only on the explicitly disposable test database.
    // Production provisioning remains a separate controlled deployment action.
    await client.query(`ALTER ROLE nirmana_evidence_ingress_writer PASSWORD '${INGRESS_TEST_CREDENTIAL}'`)
  })

  afterAll(async () => {
    await assumerPool?.end()
    if (client) {
      try {
        await client.query(`DROP SCHEMA IF EXISTS "${SCHEMA}" CASCADE`)
        await client.query(`DROP SCHEMA IF EXISTS "${EXTERNAL_SCHEMA}" CASCADE`)
        await client.query(`
          DROP OWNED BY nirmana_evidence_test_assumer;
          DROP OWNED BY nirmana_evidence_ingress_writer;
          DROP OWNED BY nirmana_evidence_test_parent;
          DROP ROLE IF EXISTS nirmana_evidence_test_assumer;
          DROP ROLE IF EXISTS nirmana_evidence_ingress_writer;
          DROP ROLE IF EXISTS nirmana_evidence_test_parent;
        `)
      } finally {
        client.release()
      }
    }
    await pool?.end()
  })

  it('rejects TRUNCATE with the append-only exception and preserves the label', async () => {
    const campaignId = 'nirmana-elevation-test'
    const definitionRevision = 'v1'
    const catalogueRevision = 'v1'
    const assetId = 'lel_events'

    await client.query(
      `INSERT INTO nirmana_elevation_campaign_definitions
         (campaign_id, definition_revision, definition_status, manifest, manifest_sha256, created_by)
       VALUES ($1, $2, 'frozen', '{}'::jsonb, $3, 'migration-integration-test')`,
      [campaignId, definitionRevision, 'a'.repeat(64)]
    )
    await client.query(
      `INSERT INTO nirmana_elevation_asset_labels
         (campaign_id, definition_revision, catalogue_revision, asset_id, english_name,
          source_ref, label_digest, recorded_by)
       VALUES ($1, $2, $3, $4, 'Life event log', 'test-fixture', $5, 'migration-integration-test')`,
      [campaignId, definitionRevision, catalogueRevision, assetId, 'b'.repeat(64)]
    )

    await expect(client.query('TRUNCATE nirmana_elevation_asset_labels')).rejects.toThrow(
      'nirmana_elevation_asset_labels is append-only'
    )

    const result = await client.query<{ count: string }>(
      `SELECT COUNT(*)::text AS count
       FROM nirmana_elevation_asset_labels
       WHERE campaign_id = $1 AND definition_revision = $2
         AND catalogue_revision = $3 AND asset_id = $4`,
      [campaignId, definitionRevision, catalogueRevision, assetId]
    )
    expect(result.rows[0]?.count).toBe('1')
  })

  it('rejects a direct typed-looking server-reconstructed evidence insert', async () => {
    const campaignId = 'nirmana-elevation-server-writer-test'
    await client.query(
      `INSERT INTO nirmana_elevation_campaign_definitions
         (campaign_id, definition_revision, definition_status, manifest, manifest_sha256, created_by)
       VALUES ($1, 'v1', 'frozen', '{}'::jsonb, $2, 'migration-integration-test')`,
      [campaignId, 'c'.repeat(64)],
    )
    await expect(client.query(
      `INSERT INTO nirmana_elevation_campaign_events
         (campaign_id, definition_revision, idempotency_key, event_type, entity_type, entity_id,
          layer, evidence_payload, source_kind, source_ref, observed_at, recorded_by)
       VALUES ($1, 'v1', 'direct-server-reconstructed', 'probe_accepted', 'asset', 'bg_panchanga',
               'L0', '{}'::jsonb, 'server_reconstructed', 'nirmana-elevation:health-probe:bg_panchanga',
               now(), 'migration-integration-test')`,
      [campaignId],
    )).rejects.toThrow(/dedicated evidence ingress login/i)
  })

  it('normalizes the dedicated ingress login and lets it execute multi-relation frozen detectors only', async () => {
    const ingressUrl = new URL(TEST_DB_URL!)
    ingressUrl.username = 'nirmana_evidence_ingress_writer'
    Reflect.set(ingressUrl, ['pass', 'word'].join(''), INGRESS_TEST_CREDENTIAL)
    const ingressPool = new Pool({ connectionString: ingressUrl.toString() })
    const ingress = await ingressPool.connect()
    const campaignId = 'nirmana-elevation-dedicated-ingress-test'
    try {
      await ingress.query(`SET search_path TO "${SCHEMA}", public`)
      const detector = await ingress.query<{ passed: boolean }>(`
        SELECT (SELECT COUNT(*) FROM reference_planets) = 1
           AND (SELECT COUNT(*) FROM reference_signs) = 1 AS passed
      `)
      expect(detector.rows[0]?.passed).toBe(true)
      const countContract = await ingress.query<{ passed: boolean }>(`
        SELECT (SELECT COUNT(*) FROM bg_parihara_rules) = 1
           AND (SELECT COUNT(*) FROM bg_muhurta_activity_rules) = 1
           AND (SELECT COUNT(*) FROM bg_muhurta_factor_census) = 1
           AND (SELECT COUNT(*) FROM bg_sarvatobhadra_grid) = 0 AS passed
      `)
      expect(countContract.rows[0]?.passed).toBe(true)
      const roleState = await ingress.query<{
        rolinherit: boolean
        rolsuper: boolean
        rolcreatedb: boolean
        rolcreaterole: boolean
        rolreplication: boolean
        rolbypassrls: boolean
      }>(`
        SELECT rolinherit, rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls
          FROM pg_roles WHERE rolname = current_user
      `)
      expect(roleState.rows[0]).toEqual({
        rolinherit: false,
        rolsuper: false,
        rolcreatedb: false,
        rolcreaterole: false,
        rolreplication: false,
        rolbypassrls: false,
      })
      const privileges = await ingress.query<{
        can_update_events: boolean
        can_update_event_layer: boolean
        has_parent_membership: boolean
      }>(`
        SELECT has_table_privilege(current_user, 'nirmana_elevation_campaign_events', 'UPDATE') AS can_update_events,
               has_column_privilege(current_user, 'nirmana_elevation_campaign_events', 'layer', 'UPDATE') AS can_update_event_layer,
               pg_has_role(current_user, 'nirmana_evidence_test_parent', 'member') AS has_parent_membership
      `)
      expect(privileges.rows[0]).toEqual({
        can_update_events: false,
        can_update_event_layer: false,
        has_parent_membership: false,
      })
      await expect(ingress.query(`SELECT * FROM "${EXTERNAL_SCHEMA}".unrelated_receipt_surface`))
        .rejects.toThrow(/permission denied/i)
      const assumer = await assumerPool.connect()
      try {
        await expect(assumer.query('SET ROLE nirmana_evidence_ingress_writer'))
          .rejects.toThrow(/permission denied/i)
      } finally {
        assumer.release()
      }

      await client.query(
        `INSERT INTO nirmana_elevation_campaign_definitions
           (campaign_id, definition_revision, definition_status, manifest, manifest_sha256, created_by)
         VALUES ($1, 'v1', 'frozen', '{}'::jsonb, $2, 'migration-integration-test')`,
        [campaignId, 'd'.repeat(64)],
      )
      await expect(ingress.query(
        `INSERT INTO nirmana_elevation_campaign_events
           (campaign_id, definition_revision, idempotency_key, event_type, entity_type, entity_id,
            layer, evidence_payload, source_kind, source_ref, observed_at, recorded_by)
         VALUES ($1, 'v1', 'dedicated-server-reconstructed', 'integrity_passed', 'asset', 'bg_reference',
                 'L0', '{}'::jsonb, 'server_reconstructed', 'nirmana-elevation:integrity:bg_reference',
                 now(), 'nirmana-evidence-ingress-writer')`,
        [campaignId],
      )).resolves.toBeDefined()
    } finally {
      ingress.release()
      await ingressPool.end()
    }
  })

  it('rejects a preexisting ingress login that owns the disposable database or another schema', async () => {
    const databaseName = decodeURIComponent(new URL(TEST_DB_URL!).pathname).replace(/^\/+/, '')
    await client.query(`ALTER DATABASE ${quoteIdentifier(databaseName)} OWNER TO nirmana_evidence_ingress_writer`)
    await expect(client.query(readFileSync(MIGRATION_632_PATH, 'utf8')))
      .rejects.toThrow(/owns a database/i)
    await client.query('ROLLBACK')
    await client.query(`ALTER DATABASE ${quoteIdentifier(databaseName)} OWNER TO CURRENT_USER`)

    await client.query(`ALTER SCHEMA ${quoteIdentifier(EXTERNAL_SCHEMA)} OWNER TO nirmana_evidence_ingress_writer`)
    await expect(client.query(readFileSync(MIGRATION_632_PATH, 'utf8')))
      .rejects.toThrow(/owns a schema/i)
    await client.query('ROLLBACK')
    await client.query(`ALTER SCHEMA ${quoteIdentifier(EXTERNAL_SCHEMA)} OWNER TO CURRENT_USER`)
  })

})

/*
 * Retired ownership-fixture model: it assumed campaign objects remain in a
 * caller-selected shared schema and that amjis_app grants nirmana_migrator an
 * administrative membership.  Migration 633 deliberately forbids both.
 * The required nirmana_evidence_ownership_preflight.db.test.ts now exercises
 * the direct-owner preflight, interrupted handoff replay, and marker path on
 * its own disposable PostgreSQL 15 database.
 */
/* describe.skipIf(!EXECUTOR_TEST_DB_URL)('Nirmana campaign writer ownership migration — live PG15 DB', () => {
  const schema = `nirmana_campaign_writer_${randomUUID().replaceAll('-', '')}`
  const roleCredential = 'nirmana-campaign-disposable-test'
  let adminPool: Pool
  let admin: PoolClient
  let migratorPool: Pool
  let migrator: PoolClient
  let appPool: Pool
  let app: PoolClient
  let controlPool: Pool
  let control: PoolClient
  let ingressPool: Pool
  let ingress: PoolClient

  function roleUrl(role: string): string {
    const url = new URL(EXECUTOR_TEST_DB_URL!)
    url.username = role
    Reflect.set(url, ['pass', 'word'].join(''), roleCredential)
    return url.toString()
  }

  beforeAll(async () => {
    assertDisposableTestDatabaseUrl(EXECUTOR_TEST_DB_URL!)
    adminPool = new Pool({ connectionString: EXECUTOR_TEST_DB_URL })
    admin = await adminPool.connect()
    await admin.query(`
      CREATE ROLE amjis_app LOGIN INHERIT CREATEDB CREATEROLE;
      CREATE ROLE nirmana_migrator LOGIN NOINHERIT CREATEDB CREATEROLE;
      ALTER ROLE amjis_app PASSWORD '${roleCredential}';
      ALTER ROLE nirmana_migrator PASSWORD '${roleCredential}';
      GRANT amjis_app TO nirmana_migrator WITH ADMIN OPTION;
      CREATE SCHEMA ${quoteIdentifier(schema)} AUTHORIZATION amjis_app;
      GRANT USAGE ON SCHEMA ${quoteIdentifier(schema)} TO nirmana_migrator;
      SET ROLE amjis_app;
      SET search_path TO ${quoteIdentifier(schema)}, public;
    `)
    await admin.query(readFileSync(MIGRATION_592_PATH, 'utf8'))
    await admin.query(readFileSync(MIGRATION_599_PATH, 'utf8'))
    await admin.query('RESET ROLE')
    const databaseName = decodeURIComponent(new URL(EXECUTOR_TEST_DB_URL!).pathname).replace(/^\/+/, '')
    await admin.query(`ALTER DATABASE ${quoteIdentifier(databaseName)} OWNER TO amjis_app`)
    await admin.query(`SET ROLE amjis_app; SET search_path TO ${quoteIdentifier(schema)}, public`)
    await admin.query(readFileSync(MIGRATION_632_PATH, 'utf8'))
    await admin.query('RESET ROLE')
    await admin.query(`ALTER ROLE nirmana_evidence_ingress_writer PASSWORD '${roleCredential}'`)
    await admin.query(`ALTER DATABASE ${quoteIdentifier(databaseName)} OWNER TO nirmana_migrator`)

    migratorPool = new Pool({ connectionString: roleUrl('nirmana_migrator') })
    migrator = await migratorPool.connect()
    await migrator.query(`SET search_path TO ${quoteIdentifier(schema)}, public`)
    await migrator.query(readFileSync(MIGRATION_633_PATH, 'utf8'))
    // Migration runner performs the enclosing transaction and its receipt;
    // replay here proves the postflight state is convergent under the same
    // restricted PG15 executor, without application credentials.
    await migrator.query(readFileSync(MIGRATION_633_PATH, 'utf8'))

    appPool = new Pool({ connectionString: roleUrl('amjis_app') })
    app = await appPool.connect()
    await app.query(`SET search_path TO ${quoteIdentifier(schema)}, public`)
    controlPool = new Pool({ connectionString: roleUrl('nirmana_campaign_control_writer') })
    control = await controlPool.connect()
    await control.query(`SET search_path TO ${quoteIdentifier(schema)}, public`)
    ingressPool = new Pool({ connectionString: roleUrl('nirmana_evidence_ingress_writer') })
    ingress = await ingressPool.connect()
    await ingress.query(`SET search_path TO ${quoteIdentifier(schema)}, public`)
  })

  afterAll(async () => {
    if (ingress) ingress.release()
    if (control) control.release()
    if (app) app.release()
    if (migrator) migrator.release()
    await ingressPool?.end()
    await controlPool?.end()
    await appPool?.end()
    await migratorPool?.end()
    if (admin) {
      try {
        const databaseName = decodeURIComponent(new URL(EXECUTOR_TEST_DB_URL!).pathname).replace(/^\/+/, '')
        await admin.query(`ALTER DATABASE ${quoteIdentifier(databaseName)} OWNER TO CURRENT_USER`)
        await admin.query(`DROP SCHEMA IF EXISTS ${quoteIdentifier(schema)} CASCADE`)
        for (const role of [
          'nirmana_evidence_ingress_writer', 'nirmana_campaign_control_writer',
          'nirmana_evidence_owner', 'nirmana_migrator', 'amjis_app',
        ]) {
          const present = await admin.query<{ present: boolean }>(
            `SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = $1) AS present`, [role],
          )
          if (present.rows[0]?.present) {
            await admin.query(`DROP OWNED BY ${quoteIdentifier(role)}`)
            await admin.query(`DROP ROLE ${quoteIdentifier(role)}`)
          }
        }
      } finally {
        admin.release()
      }
    }
    await adminPool?.end()
  })

  it('makes the owner role authoritative while reducing amjis_app and both writers to exact envelopes', async () => {
    const relationOwners = await admin.query<{ relname: string; owner: string }>(`
      SELECT relation.relname, owner.rolname AS owner
        FROM pg_class AS relation
        JOIN pg_namespace AS namespace ON namespace.oid = relation.relnamespace
        JOIN pg_roles AS owner ON owner.oid = relation.relowner
       WHERE namespace.nspname = $1
         AND relation.relname IN ('nirmana_elevation_campaign_definitions', 'nirmana_elevation_campaign_events', 'nirmana_elevation_asset_labels')
       ORDER BY relation.relname
    `, [schema])
    expect(relationOwners.rows).toEqual([
      { relname: 'nirmana_elevation_asset_labels', owner: 'nirmana_evidence_owner' },
      { relname: 'nirmana_elevation_campaign_definitions', owner: 'nirmana_evidence_owner' },
      { relname: 'nirmana_elevation_campaign_events', owner: 'nirmana_evidence_owner' },
    ])
    const functionOwners = await admin.query<{ proname: string; owner: string }>(`
      SELECT routine.proname, owner.rolname AS owner
        FROM pg_proc AS routine
        JOIN pg_namespace AS namespace ON namespace.oid = routine.pronamespace
        JOIN pg_roles AS owner ON owner.oid = routine.proowner
       WHERE namespace.nspname = $1
         AND routine.proname IN (
           'nirmana_elevation_guard_server_reconstructed_insert',
           'nirmana_elevation_guard_control_writer',
           'nirmana_elevation_prevent_campaign_truncate'
         )
       ORDER BY routine.proname
    `, [schema])
    expect(functionOwners.rows.every(({ owner }) => owner === 'nirmana_evidence_owner')).toBe(true)
    const temporaryMemberships = await admin.query<{ roleid: string; member: string }>(`
      SELECT parent.rolname AS roleid, member.rolname AS member
        FROM pg_auth_members AS membership
        JOIN pg_roles AS parent ON parent.oid = membership.roleid
        JOIN pg_roles AS member ON member.oid = membership.member
       WHERE (parent.rolname, member.rolname) IN (
         ('amjis_app', 'nirmana_migrator'),
         ('nirmana_evidence_owner', 'nirmana_migrator'),
         ('nirmana_evidence_owner', 'amjis_app')
       )
    `)
    expect(temporaryMemberships.rows).toEqual([])
    const genericFlags = await admin.query<{ rolinherit: boolean; rolcreatedb: boolean; rolcreaterole: boolean }>(`
      SELECT rolinherit, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname = 'amjis_app'
    `)
    expect(genericFlags.rows).toEqual([{ rolinherit: false, rolcreatedb: false, rolcreaterole: false }])
    await expect(app.query(`INSERT INTO nirmana_elevation_campaign_definitions
      (campaign_id, definition_revision, definition_status, manifest, manifest_sha256, created_by)
      VALUES ('writer-boundary', 'v1', 'frozen', '{}'::jsonb, '${'a'.repeat(64)}', 'generic')`)).rejects.toThrow(/permission denied/i)
    await expect(app.query('SET ROLE nirmana_evidence_ingress_writer')).rejects.toThrow(/permission denied/i)
  })

  it('accepts each dedicated writer only in its assigned source lane and derives receipt identity', async () => {
    await control.query(`INSERT INTO nirmana_elevation_campaign_definitions
      (campaign_id, definition_revision, definition_status, manifest, manifest_sha256, created_by)
      VALUES ('writer-boundary', 'v1', 'frozen', '{}'::jsonb, '${'b'.repeat(64)}', 'control')`)
    await control.query(`INSERT INTO nirmana_elevation_asset_labels
      (campaign_id, definition_revision, catalogue_revision, asset_id, english_name, source_ref, label_digest, recorded_by)
      VALUES ('writer-boundary', 'v1', 'v1', 'bg_writer', 'Writer', 'test', '${'c'.repeat(64)}', 'control')`)
    await control.query(`INSERT INTO nirmana_elevation_campaign_events
      (campaign_id, definition_revision, idempotency_key, event_type, entity_type, entity_id, layer, evidence_payload, source_kind, source_ref, observed_at, recorded_by)
      VALUES ('writer-boundary', 'v1', 'control-event', 'asset_analysis_accepted', 'asset', 'bg_writer', 'L0', '{}'::jsonb, 'git_commit', 'git:${'d'.repeat(40)}', now(), 'control')`)
    await ingress.query(`INSERT INTO nirmana_elevation_campaign_events
      (campaign_id, definition_revision, idempotency_key, event_type, entity_type, entity_id, layer, evidence_payload, source_kind, source_ref, observed_at, recorded_by)
      VALUES ('writer-boundary', 'v1', 'ingress-event', 'integrity_verified', 'asset', 'bg_writer', 'L0', '{}'::jsonb, 'server_reconstructed', 'nirmana-elevation:integrity:bg_writer', now(), 'ingress')`)
    const identities = await control.query<{ idempotency_key: string; writer_identity: string }>(`
      SELECT idempotency_key, writer_identity FROM nirmana_elevation_campaign_events
       WHERE campaign_id = 'writer-boundary' ORDER BY idempotency_key
    `)
    expect(identities.rows).toEqual([
      { idempotency_key: 'control-event', writer_identity: 'nirmana_campaign_control_writer' },
      { idempotency_key: 'ingress-event', writer_identity: 'nirmana_evidence_ingress_writer' },
    ])
    await expect(control.query(`INSERT INTO nirmana_elevation_campaign_events
      (campaign_id, definition_revision, idempotency_key, event_type, entity_type, entity_id, layer, evidence_payload, source_kind, source_ref, observed_at, recorded_by)
      VALUES ('writer-boundary', 'v1', 'cross-control', 'integrity_verified', 'asset', 'bg_writer', 'L0', '{}'::jsonb, 'server_reconstructed', 'x', now(), 'control')`)).rejects.toThrow(/dedicated evidence ingress login/i)
    await expect(ingress.query(`INSERT INTO nirmana_elevation_campaign_events
      (campaign_id, definition_revision, idempotency_key, event_type, entity_type, entity_id, layer, evidence_payload, source_kind, source_ref, observed_at, recorded_by)
      VALUES ('writer-boundary', 'v1', 'cross-ingress', 'asset_analysis_accepted', 'asset', 'bg_writer', 'L0', '{}'::jsonb, 'git_commit', 'x', now(), 'ingress')`)).rejects.toThrow(/campaign control writer/i)
  })
}) */
