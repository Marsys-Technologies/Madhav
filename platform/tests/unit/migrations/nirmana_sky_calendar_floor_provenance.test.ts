import fs from 'node:fs'
import path from 'node:path'
import { Client } from 'pg'
import { describe, expect, it } from 'vitest'

import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

const migrationPath = path.resolve(
  process.cwd(),
  'supabase/migrations/605_nirmana_sky_calendar_floor_provenance.sql',
)
const migration = fs.readFileSync(migrationPath, 'utf8')

const LEGACY_EXPLANATION = 'Live-verified 2026-07-29 against a real throwaway Postgres: 28,760 ingress + 1,674 station + 308 eclipse_solar + 312 eclipse_lunar + 10 double_transit = 31,064, over horizon 1900-01-01 -> 2036-07-29 (today+10y at verification time). A later build reads >= this count as the forward edge rolls forward (never less).'
const CORRECTED_EXPLANATION = '31,059 achieved rows in the authoritative 2026-08-02 production build using the pinned Swiss Ephemeris file corpus on Linux/x86_64: 28,755 ingress + 1,674 station + 308 eclipse_solar + 312 eclipse_lunar + 10 double_transit. This is an achieved baseline, not a forecast; explicit rolling-horizon rebuilds may increase it.'

describe('migration 605 — sky-calendar floor provenance', () => {
  it('keeps the canonical seed aligned with the corrected production baseline', () => {
    const asset = ASSETS.find((candidate) => candidate.asset_id === 'bg_sky_calendar')
    expect(asset?.target_floor).toBe(31059)
    expect(asset?.volume_explanation).toBe(CORRECTED_EXPLANATION)
    expect(asset?.target_table).toBe('bg_sky_calendar')
    expect(asset?.count_sql).toBe('SELECT COUNT(*) FROM bg_sky_calendar')
    expect(asset?.size_sql).toBe("SELECT pg_total_relation_size('bg_sky_calendar')")
  })

  it('accepts only the exact legacy or corrected contract and leaves transactions to the runner', () => {
    expect(migration).toContain(LEGACY_EXPLANATION)
    expect(migration).toContain(CORRECTED_EXPLANATION)
    expect(migration).toContain("registry_row.target_floor = 31064")
    expect(migration).toContain("registry_row.target_floor = 31059")
    expect(migration).toContain("migration 605 refuses unknown bg_sky_calendar registry contract")
    expect(migration).not.toMatch(/^BEGIN;/m)
    expect(migration).not.toMatch(/^COMMIT;/m)
  })
})

const TEST_DATABASE_URL = process.env.NIRMANA_SKY_CALENDAR_FLOOR_TEST_DATABASE_URL

if (TEST_DATABASE_URL) {
  const parsed = new URL(TEST_DATABASE_URL)
  if (!['localhost', '127.0.0.1'].includes(parsed.hostname)
    || parsed.pathname !== '/nirmana_sky_calendar_floor_test') {
    throw new Error(
      'NIRMANA_SKY_CALENDAR_FLOOR_TEST_DATABASE_URL must point to the exact local '
      + 'nirmana_sky_calendar_floor_test database',
    )
  }
}

describe.skipIf(!TEST_DATABASE_URL)('migration 605 — real Postgres behavior', () => {
  async function connectPrepared(state: 'legacy' | 'corrected' = 'legacy'): Promise<Client> {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    await client.query(`
      CREATE TEMP TABLE asset_registry (
        asset_id text PRIMARY KEY,
        target_table text,
        count_sql text,
        size_sql text,
        is_active boolean,
        has_writer boolean,
        catalog_status text,
        asset_kind text,
        target_floor bigint,
        volume_explanation text
      );
    `)
    await client.query(
      `INSERT INTO asset_registry
        (asset_id, target_table, count_sql, size_sql, is_active, has_writer,
         catalog_status, asset_kind, target_floor, volume_explanation)
       VALUES
        ('bg_sky_calendar', 'bg_sky_calendar',
         'SELECT COUNT(*) FROM bg_sky_calendar',
         'SELECT pg_total_relation_size(''bg_sky_calendar'')',
         true, true, 'CURRENT', 'data', $1, $2)`,
      state === 'legacy'
        ? [31064, LEGACY_EXPLANATION]
        : [31059, CORRECTED_EXPLANATION],
    )
    return client
  }

  it('converts the legacy row and replays exactly', async () => {
    const client = await connectPrepared()
    try {
      await client.query(migration)
      await client.query(migration)
      const result = await client.query(
        `SELECT target_floor, volume_explanation FROM asset_registry
         WHERE asset_id = 'bg_sky_calendar'`,
      )
      expect(result.rows).toEqual([{
        target_floor: '31059',
        volume_explanation: CORRECTED_EXPLANATION,
      }])
    } finally {
      await client.end()
    }
  })

  it('accepts a canonical fresh-replay row without changing it', async () => {
    const client = await connectPrepared('corrected')
    try {
      await client.query(migration)
      const result = await client.query(
        `SELECT target_floor, volume_explanation FROM asset_registry
         WHERE asset_id = 'bg_sky_calendar'`,
      )
      expect(result.rows).toEqual([{
        target_floor: '31059',
        volume_explanation: CORRECTED_EXPLANATION,
      }])
    } finally {
      await client.end()
    }
  })

  it('rejects nullable registry drift without applying the correction', async () => {
    const client = await connectPrepared()
    try {
      await client.query(
        `UPDATE asset_registry SET catalog_status = NULL
         WHERE asset_id = 'bg_sky_calendar'`,
      )
      await expect(client.query(migration)).rejects.toThrow(
        'migration 605 refuses unknown bg_sky_calendar registry contract',
      )
      const result = await client.query(
        `SELECT target_floor, volume_explanation FROM asset_registry
         WHERE asset_id = 'bg_sky_calendar'`,
      )
      expect(result.rows).toEqual([{
        target_floor: '31064',
        volume_explanation: LEGACY_EXPLANATION,
      }])
    } finally {
      await client.end()
    }
  })

  it('rolls the metadata correction back with the runner-owned transaction', async () => {
    const client = await connectPrepared()
    try {
      await client.query('BEGIN')
      await client.query(migration)
      await client.query('ROLLBACK')
      const result = await client.query(
        `SELECT target_floor, volume_explanation FROM asset_registry
         WHERE asset_id = 'bg_sky_calendar'`,
      )
      expect(result.rows).toEqual([{
        target_floor: '31064',
        volume_explanation: LEGACY_EXPLANATION,
      }])
    } finally {
      await client.end()
    }
  })
})
