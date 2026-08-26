// @vitest-environment node
import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { Pool } from 'pg'

const databaseUrl = process.env.NIRMANA_MONITOR_TEST_DATABASE_URL
const run = databaseUrl ? describe : describe.skip
const migrationPath = resolve(process.cwd(), 'migrations/629_nirmana_elevation_monitor_observations.sql')
const migrationSql = readFileSync(migrationPath, 'utf8')
const digest = 'a'.repeat(64)

run('migration 629 Nirmana monitor database contract', () => {
  let pool: Pool

  beforeAll(async () => {
    const parsed = new URL(databaseUrl!)
    if (!['localhost', '127.0.0.1'].includes(parsed.hostname) || parsed.pathname !== '/nirmana_monitor_test') {
      throw new Error('NIRMANA_MONITOR_TEST_DATABASE_URL must target local database nirmana_monitor_test')
    }
    pool = new Pool({ connectionString: databaseUrl })
    await pool.query(`
      DROP TABLE IF EXISTS nirmana_elevation_monitor_observations CASCADE;
      DROP FUNCTION IF EXISTS nirmana_elevation_monitor_sorted_unique(text[]) CASCADE;
      DROP FUNCTION IF EXISTS nirmana_elevation_prevent_monitor_observation_mutation() CASCADE;
    `)
    await pool.query(migrationSql)
    await pool.query(migrationSql)
  })

  afterAll(async () => {
    if (!pool) return
    await pool.query(`
      DROP TABLE IF EXISTS nirmana_elevation_monitor_observations CASCADE;
      DROP FUNCTION IF EXISTS nirmana_elevation_monitor_sorted_unique(text[]) CASCADE;
      DROP FUNCTION IF EXISTS nirmana_elevation_prevent_monitor_observation_mutation() CASCADE;
    `)
    await pool.end()
  })

  async function insert(overrides: Record<string, unknown> = {}) {
    const row = {
      status: 'in_sync', affected_asset_ids: ['bg_alpha', 'bg_beta'],
      current_definition_sha256: digest, candidate_definition_sha256: digest,
      registry_identity_sha256: digest, registry_contract_sha256: digest,
      candidate_catalogue_sha256: digest, selected_catalogue_sha256: digest,
      runtime_sha256: digest, release_sha256: digest, source_state: 'available',
      source_observed_at: '2026-08-26T09:00:00.000Z', source_age_seconds: 0,
      freshness_state: 'fresh', freshness_deadline_at: '2026-08-26T09:15:00.000Z',
      runtime_liveness: 'quiet', release_state: 'in_sync',
      release_observed_at: '2026-08-26T09:00:00.000Z', release_age_seconds: 0,
      public_detail: 'Program sources are synchronized.', source_error_code: null,
      ...overrides,
    }
    return pool.query(
      `INSERT INTO nirmana_elevation_monitor_observations
       (status, affected_asset_ids, current_definition_sha256, candidate_definition_sha256,
        registry_identity_sha256, registry_contract_sha256, candidate_catalogue_sha256,
        selected_catalogue_sha256, runtime_sha256, release_sha256, source_state,
        source_observed_at, source_age_seconds, freshness_state, freshness_deadline_at,
        runtime_liveness, release_state, release_observed_at, release_age_seconds,
        public_detail, source_error_code)
       VALUES ($1, $2::text[], $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
               $14, $15, $16, $17, $18, $19, $20, $21) RETURNING id`,
      [
        row.status, row.affected_asset_ids, row.current_definition_sha256,
        row.candidate_definition_sha256, row.registry_identity_sha256,
        row.registry_contract_sha256, row.candidate_catalogue_sha256,
        row.selected_catalogue_sha256, row.runtime_sha256, row.release_sha256,
        row.source_state, row.source_observed_at, row.source_age_seconds,
        row.freshness_state, row.freshness_deadline_at, row.runtime_liveness,
        row.release_state, row.release_observed_at, row.release_age_seconds,
        row.public_detail, row.source_error_code,
      ],
    )
  }

  it.each([
    ['unsorted', ['bg_beta', 'bg_alpha']],
    ['duplicate', ['bg_alpha', 'bg_alpha']],
  ])('rejects %s affected asset IDs in PostgreSQL', async (_case, affectedAssetIds) => {
    await expect(insert({ affected_asset_ids: affectedAssetIds })).rejects.toThrow(/affected_asset_ids|check constraint/i)
  })

  it('rejects incomplete digest state for a successful authoritative observation', async () => {
    await expect(insert({ candidate_definition_sha256: null })).rejects.toThrow(/digest|check constraint/i)
  })

  it('rejects stale digests on a source-unavailable observation', async () => {
    await expect(insert({
      status: 'source_unavailable', source_state: 'unavailable', source_observed_at: null,
      source_age_seconds: null, freshness_state: 'unavailable', freshness_deadline_at: null,
      runtime_liveness: 'unavailable', release_state: 'unavailable', release_observed_at: null,
      release_age_seconds: null, source_error_code: 'NIRMANA_SOURCE_UNAVAILABLE',
    })).rejects.toThrow(/digest|check constraint/i)
  })

  it('accepts the honest baseline-missing null shape and rejects later mutation', async () => {
    const inserted = await insert({
      status: 'baseline_missing', current_definition_sha256: null,
      public_detail: 'No accepted frozen program definition exists.',
    })
    await expect(pool.query(
      `UPDATE nirmana_elevation_monitor_observations SET public_detail = 'changed' WHERE id = $1`,
      [inserted.rows[0].id],
    )).rejects.toThrow(/append-only/i)
  })

  it('accepts an all-null unavailable digest shape with explicit unavailable state', async () => {
    await expect(insert({
      status: 'source_unavailable', affected_asset_ids: [], current_definition_sha256: null,
      candidate_definition_sha256: null, registry_identity_sha256: null,
      registry_contract_sha256: null, candidate_catalogue_sha256: null,
      selected_catalogue_sha256: null, runtime_sha256: null, release_sha256: null,
      source_state: 'unavailable', source_observed_at: null, source_age_seconds: null,
      freshness_state: 'unavailable', freshness_deadline_at: null,
      runtime_liveness: 'unavailable', release_state: 'unavailable',
      release_observed_at: null, release_age_seconds: null,
      public_detail: 'Authoritative source is unavailable.',
      source_error_code: 'NIRMANA_SOURCE_UNAVAILABLE',
    })).resolves.toMatchObject({ rowCount: 1 })
  })
})
