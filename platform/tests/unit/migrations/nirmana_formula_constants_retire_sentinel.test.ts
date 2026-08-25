import fs from 'node:fs'
import path from 'node:path'
import { Client } from 'pg'
import { describe, expect, it } from 'vitest'

const migrationPath = path.resolve(
  process.cwd(),
  'supabase/migrations/603_nirmana_formula_constants_retire_sentinel.sql',
)
const migration = fs.readFileSync(migrationPath, 'utf8')

const SENTINEL_VALUE = {
  bug: 'ka_sangam stores confidence as convergence score (0-1) but this field is not a prediction confidence — it is a dasha/transit alignment strength. These are different quantities.',
  fix: 'W4A: separate convergence_strength from prediction_confidence in ka_sangam output',
  status: 'OPEN',
}
const SENTINEL_CITATION =
  'W1_SEED_PACKAGE_v1_0 §7 BA_MASTER C10: CONFLATION-BUG — fix at source in W4A. Do NOT seed as a constant.'
const LEGACY_DESCRIPTION =
  'Canonical formula constants registry — combustion orbs, obstruction thresholds, magnitude tiers, dignity scores, house weights, attention budget, and engineering constants. Classes: CLASSICAL (cite, never tune) | NATIVE_JUDGMENT (versioned, L5-calibratable) | ENGINEERING | CONFLATION_BUG.'

describe('migration 603 — retire resolved formula-constant sentinel', () => {
  it('locks and exactly matches the resolved non-operational sentinel', () => {
    expect(migration).toContain("constant_id = '_bug_ka_sangam_confidence_conflation'")
    expect(migration).toContain("class = 'conflation_bug'")
    expect(migration).toContain('FOR UPDATE')
    expect(migration).toContain(JSON.stringify(SENTINEL_VALUE))
    expect(migration).toContain(SENTINEL_CITATION)
    expect(migration).toContain('migration 603 refuses unknown formula-constant sentinel contract')
    expect(migration).toContain('GET DIAGNOSTICS deleted_rows = ROW_COUNT')
    expect(migration).toContain('IF deleted_rows <> 1 THEN')
  })

  it('leaves transaction ownership with the migration runner', () => {
    expect(migration).not.toMatch(/^BEGIN;/m)
    expect(migration).not.toMatch(/^COMMIT;/m)
  })

  it('canonicalizes and postflights all registry measurement metadata', () => {
    expect(migration).toContain('migration 603 refuses unknown bg_formula_constants registry contract')
    expect(migration).toContain('migration 603 failed bg_formula_constants registry postflight')
    expect(migration).toContain('SET target_floor = 17')
    expect(migration).toContain("count_sql = 'SELECT count(*) FROM brahma_formula_constants'")
    expect(migration).toContain('17 governed constants')
  })
})

const TEST_DATABASE_URL = process.env.NIRMANA_FORMULA_CONSTANTS_TEST_DATABASE_URL

if (TEST_DATABASE_URL) {
  const parsed = new URL(TEST_DATABASE_URL)
  if (!['localhost', '127.0.0.1'].includes(parsed.hostname)
    || parsed.pathname !== '/nirmana_formula_constants_test') {
    throw new Error(
      'NIRMANA_FORMULA_CONSTANTS_TEST_DATABASE_URL must point to the exact local '
      + 'nirmana_formula_constants_test database',
    )
  }
}

describe.skipIf(!TEST_DATABASE_URL)('migration 603 — real Postgres behavior', () => {
  async function prepare(client: Client) {
    await client.query(`
      CREATE TEMP TABLE brahma_formula_constants (
        constant_id text PRIMARY KEY,
        value_jsonb jsonb NOT NULL,
        class text NOT NULL,
        consumer_assets text[] NOT NULL DEFAULT '{}',
        citation_or_ratification text NOT NULL,
        calibratable boolean NOT NULL DEFAULT false,
        bounds jsonb,
        version text NOT NULL DEFAULT '1.0'
      );
      CREATE TEMP TABLE asset_registry (
        asset_id text PRIMARY KEY,
        target_floor integer,
        count_sql text,
        volume_explanation text,
        english_description text
      );
      INSERT INTO brahma_formula_constants
        (constant_id, value_jsonb, class, citation_or_ratification)
      SELECT 'governed_' || n, '{}'::jsonb, 'engineering', 'fixture'
      FROM generate_series(1, 17) AS n;
    `)
    await client.query(
      `INSERT INTO asset_registry
        (asset_id, target_floor, count_sql, volume_explanation, english_description)
       VALUES
        ('bg_formula_constants', NULL,
         'SELECT COUNT(*) FROM brahma_formula_constants WHERE class != ''conflation_bug''',
         NULL, $1)`,
      [LEGACY_DESCRIPTION],
    )
    await client.query(
      `INSERT INTO brahma_formula_constants
        (constant_id, value_jsonb, class, consumer_assets,
         citation_or_ratification, calibratable, bounds, version)
       VALUES
        ('_bug_ka_sangam_confidence_conflation', $1::jsonb,
         'conflation_bug', ARRAY[]::text[], $2, false, NULL, '1.0')`,
      [JSON.stringify(SENTINEL_VALUE), SENTINEL_CITATION],
    )
  }

  async function connectPrepared(): Promise<Client> {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    await prepare(client)
    return client
  }

  it('retires one exact sentinel, preserves 17 rows, and replays idempotently', async () => {
    const client = await connectPrepared()
    try {
      await client.query(migration)
      await client.query(migration)

      const constants = await client.query(
        `SELECT count(*)::int AS count,
                count(*) FILTER (WHERE class = 'conflation_bug')::int AS sentinels
         FROM brahma_formula_constants`,
      )
      expect(constants.rows[0]).toEqual({ count: 17, sentinels: 0 })

      const registry = await client.query(
        `SELECT target_floor, count_sql, volume_explanation, english_description
         FROM asset_registry WHERE asset_id = 'bg_formula_constants'`,
      )
      expect(registry.rows[0]).toEqual({
        target_floor: 17,
        count_sql: 'SELECT count(*) FROM brahma_formula_constants',
        volume_explanation: expect.stringContaining('17 governed constants'),
        english_description: expect.stringContaining('must not be operationalized'),
      })
    } finally {
      await client.end()
    }
  })

  it('rolls the data change back with the runner-owned transaction', async () => {
    const client = await connectPrepared()
    try {
      await client.query('BEGIN')
      await client.query(migration)
      await client.query('ROLLBACK')

      const constants = await client.query(
        `SELECT count(*)::int AS count,
                count(*) FILTER (WHERE class = 'conflation_bug')::int AS sentinels
         FROM brahma_formula_constants`,
      )
      expect(constants.rows[0]).toEqual({ count: 18, sentinels: 1 })
      const registry = await client.query(
        `SELECT target_floor, count_sql
         FROM asset_registry WHERE asset_id = 'bg_formula_constants'`,
      )
      expect(registry.rows[0]).toEqual({
        target_floor: null,
        count_sql: "SELECT COUNT(*) FROM brahma_formula_constants WHERE class != 'conflation_bug'",
      })
    } finally {
      await client.end()
    }
  })

  it.each([
    ['value JSON', async (client: Client) => {
      await client.query(
        `UPDATE brahma_formula_constants
         SET value_jsonb = value_jsonb || '{"unexpected":true}'::jsonb
         WHERE constant_id = '_bug_ka_sangam_confidence_conflation'`,
      )
    }],
    ['citation', async (client: Client) => {
      await client.query(
        `UPDATE brahma_formula_constants
         SET citation_or_ratification = citation_or_ratification || ' drift'
         WHERE constant_id = '_bug_ka_sangam_confidence_conflation'`,
      )
    }],
  ])('rejects changed sentinel %s without deleting it', async (_name, mutate) => {
    const client = await connectPrepared()
    try {
      await mutate(client)
      await expect(client.query(migration)).rejects.toThrow(
        'migration 603 refuses unknown formula-constant sentinel contract',
      )
      const rows = await client.query(
        `SELECT count(*)::int AS count FROM brahma_formula_constants`,
      )
      expect(rows.rows[0].count).toBe(18)
    } finally {
      await client.end()
    }
  })

  it('rejects registry drift and rolls back sentinel deletion', async () => {
    const client = await connectPrepared()
    try {
      await client.query(
        `UPDATE asset_registry SET target_floor = 999
         WHERE asset_id = 'bg_formula_constants'`,
      )
      await expect(client.query(migration)).rejects.toThrow(
        'migration 603 refuses unknown bg_formula_constants registry contract',
      )
      const constants = await client.query(
        `SELECT count(*)::int AS count,
                count(*) FILTER (WHERE class = 'conflation_bug')::int AS sentinels
         FROM brahma_formula_constants`,
      )
      expect(constants.rows[0]).toEqual({ count: 18, sentinels: 1 })
    } finally {
      await client.end()
    }
  })

  it('rejects nullable registry drift and rolls back sentinel deletion', async () => {
    const client = await connectPrepared()
    try {
      await client.query(
        `UPDATE asset_registry SET count_sql = NULL
         WHERE asset_id = 'bg_formula_constants'`,
      )
      await expect(client.query(migration)).rejects.toThrow(
        'migration 603 refuses unknown bg_formula_constants registry contract',
      )
      const constants = await client.query(
        `SELECT count(*)::int AS count,
                count(*) FILTER (WHERE class = 'conflation_bug')::int AS sentinels
         FROM brahma_formula_constants`,
      )
      expect(constants.rows[0]).toEqual({ count: 18, sentinels: 1 })
    } finally {
      await client.end()
    }
  })
})
