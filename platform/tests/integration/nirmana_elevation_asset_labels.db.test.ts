// @vitest-environment node
/**
 * Live migration behavior test for the Nirmana elevation asset-label catalogue.
 *
 * This suite is deliberately opt-in: it reads only
 * NIRMANA_ELEVATION_TEST_DATABASE_URL and never falls back to DATABASE_URL.
 * The target must be a disposable database; the suite creates and drops an
 * isolated schema while applying the real migrations 592 and 599.
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
const MIGRATION_592_PATH = resolve(
  __dirname,
  '../../migrations/592_nirmana_elevation_campaign_evidence.sql'
)
const MIGRATION_599_PATH = resolve(
  __dirname,
  '../../migrations/599_nirmana_elevation_asset_labels.sql'
)

let pool: Pool
let client: PoolClient

describe.skipIf(!TEST_DB_URL)('Nirmana elevation asset-label append-only migration — live DB', () => {
  beforeAll(async () => {
    if (!/nirmana_elevation_test/.test(TEST_DB_URL!)) {
      throw new Error(
        'NIRMANA_ELEVATION_TEST_DATABASE_URL must point at a disposable database named ' +
          '`nirmana_elevation_test`. This suite creates and drops an isolated schema and ' +
          'must never run against production.'
      )
    }

    pool = new Pool({ connectionString: TEST_DB_URL })
    client = await pool.connect()
    await client.query(`CREATE SCHEMA "${SCHEMA}"`)
    await client.query(`SET search_path TO "${SCHEMA}", public`)
    await client.query(readFileSync(MIGRATION_592_PATH, 'utf8'))
    await client.query(readFileSync(MIGRATION_599_PATH, 'utf8'))
  })

  afterAll(async () => {
    if (client) {
      try {
        await client.query(`DROP SCHEMA IF EXISTS "${SCHEMA}" CASCADE`)
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
})
