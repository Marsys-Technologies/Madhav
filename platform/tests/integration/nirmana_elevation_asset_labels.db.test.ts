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
const SCHEMA = `nirmana_elevation_labels_test_${randomUUID().replaceAll('-', '')}`
const EXTERNAL_SCHEMA = `nirmana_elevation_external_${randomUUID().replaceAll('-', '')}`
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

function assertDisposableTestDatabaseUrl(databaseUrl: string): void {
  const databaseName = decodeURIComponent(new URL(databaseUrl).pathname).replace(/^\/+/, '')
  if (!databaseName.includes('nirmana_elevation_test')) {
    throw new Error(
      'NIRMANA_ELEVATION_TEST_DATABASE_URL must point at a disposable database named ' +
        '`nirmana_elevation_test`. This suite creates and drops an isolated schema and ' +
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
      .toThrow('NIRMANA_ELEVATION_TEST_DATABASE_URL must point at a disposable database')
    expect(() => assertDisposableTestDatabaseUrl('postgresql://db.example/nirmana%5Felevation%5Ftest'))
      .not.toThrow()
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
        LOGIN INHERIT SUPERUSER CREATEDB CREATEROLE REPLICATION BYPASSRLS;
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
    if (client) {
      try {
        await client.query(`DROP SCHEMA IF EXISTS "${SCHEMA}" CASCADE`)
        await client.query(`DROP SCHEMA IF EXISTS "${EXTERNAL_SCHEMA}" CASCADE`)
      } finally {
        client.release()
      }
    }
    await assumerPool?.end()
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
