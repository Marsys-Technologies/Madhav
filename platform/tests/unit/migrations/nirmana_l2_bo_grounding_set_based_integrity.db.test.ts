import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { Client } from 'pg'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

const DB_URL = process.env.NIRMANA_BO_GROUNDING_INTEGRITY_TEST_DATABASE_URL
if (DB_URL) {
  const parsed = new URL(DB_URL)
  if (!['127.0.0.1', 'localhost'].includes(parsed.hostname)) {
    throw new Error('NIRMANA_BO_GROUNDING_INTEGRITY_TEST_DATABASE_URL must use a localhost proxy')
  }
}

const migrationSql = readFileSync(
  join(process.cwd(), 'migrations/1032_nirmana_l2_bo_grounding_set_based_integrity.sql'),
  'utf8',
)
const legacySql = readFileSync(
  join(process.cwd(), 'migrations/899_nirmana_l2_bo_grounding_registry_row.sql'),
  'utf8',
).split('$ICHECK$')[1]

describe.skipIf(!DB_URL)('migration 1032: real PostgreSQL detector semantics', () => {
  const chart = '482012f1-710e-4a25-994a-93821f5871aa'
  const unbuiltChart = '00000000-0000-0000-0000-000000000099'
  const aya = 'lahiri_chitrapaksha'
  const signal1 = '00000000-0000-0000-0000-000000000001'
  const signal2 = '00000000-0000-0000-0000-000000000002'
  let client: Client
  let detectorSql: string

  beforeAll(async () => {
    client = new Client({ connectionString: DB_URL })
    await client.connect()
    await client.query(`
      CREATE TEMP TABLE asset_registry (
        asset_id text PRIMARY KEY,
        integrity_check_sql text
      );
      CREATE TEMP TABLE bodha_grounding_matches (
        chart_id uuid NOT NULL,
        ayanamsha_id text NOT NULL,
        target_kind text NOT NULL,
        target_id text NOT NULL,
        grounding_tier text NOT NULL,
        matched_rule_id text
      );
      CREATE TEMP TABLE bodha_msr_signals (
        signal_id uuid PRIMARY KEY,
        chart_id uuid NOT NULL,
        ayanamsha_id text NOT NULL
      );
      CREATE TEMP TABLE ga_yoga_firings (
        id integer PRIMARY KEY,
        chart_id uuid NOT NULL,
        ayanamsha_id text NOT NULL,
        fired boolean NOT NULL
      );
    `)

    const persistence = await client.query<{ relname: string; relpersistence: string }>(`
      SELECT c.relname, c.relpersistence
        FROM pg_class c
       WHERE c.oid IN (
         'asset_registry'::regclass,
         'bodha_grounding_matches'::regclass,
         'bodha_msr_signals'::regclass,
         'ga_yoga_firings'::regclass
       )
    `)
    expect(persistence.rows).toHaveLength(4)
    expect(persistence.rows.every(row => row.relpersistence === 't')).toBe(true)

    await client.query('INSERT INTO asset_registry VALUES ($1, $2)', ['bo_grounding', legacySql])
    await client.query(
      `INSERT INTO bodha_msr_signals VALUES
        ($1, $3, $4), ($2, $3, $4),
        ('00000000-0000-0000-0000-000000000098', $5, $4)`,
      [signal1, signal2, chart, aya, unbuiltChart],
    )
    await client.query(
      'INSERT INTO ga_yoga_firings VALUES (1, $1, $2, true), (2, $1, $2, false)',
      [chart, aya],
    )
    await client.query(
      `INSERT INTO bodha_grounding_matches VALUES
        ($1, $2, 'msr_signal', $3, 'pratyaksa', NULL),
        ($1, $2, 'msr_signal', $4, 'pratyaksa', NULL),
        ($1, $2, 'yoga_dosha_firing', '1', 'yukti', 'rule-1')`,
      [chart, aya, signal1, signal2],
    )

    await client.query(migrationSql)
    const installed = await client.query<{ integrity_check_sql: string }>(
      "SELECT integrity_check_sql FROM asset_registry WHERE asset_id = 'bo_grounding'",
    )
    detectorSql = installed.rows[0].integrity_check_sql
  })

  afterAll(async () => {
    await client?.end()
  })

  async function integrity(): Promise<boolean> {
    const result = await client.query<{ integrity_ok: boolean }>(
      `SELECT detector.integrity_ok FROM (${detectorSql}) AS detector(integrity_ok)`,
    )
    return result.rows[0].integrity_ok
  }

  it('is green for complete data and vacuously ignores a wholly unbuilt chart', async () => {
    expect(await integrity()).toBe(true)
  })

  it('accepts an existing non-fired yoga as non-orphan without requiring it', async () => {
    await client.query(
      `INSERT INTO bodha_grounding_matches
       VALUES ($1, $2, 'yoga_dosha_firing', '2', 'yukti', 'rule-2')`,
      [chart, aya],
    )
    expect(await integrity()).toBe(true)
    await client.query("DELETE FROM bodha_grounding_matches WHERE target_kind='yoga_dosha_firing' AND target_id='2'")
  })

  it('fails on orphan, missing, duplicate, vocabulary, and sruti-evidence corruption', async () => {
    await client.query(
      `INSERT INTO bodha_grounding_matches
       VALUES ($1, $2, 'msr_signal', '00000000-0000-0000-0000-000000000000', 'pratyaksa', NULL)`,
      [chart, aya],
    )
    expect(await integrity()).toBe(false)
    await client.query("DELETE FROM bodha_grounding_matches WHERE target_id='00000000-0000-0000-0000-000000000000'")

    await client.query('DELETE FROM bodha_grounding_matches WHERE target_id=$1', [signal2])
    expect(await integrity()).toBe(false)
    await client.query(
      `INSERT INTO bodha_grounding_matches VALUES ($1, $2, 'msr_signal', $3, 'pratyaksa', NULL)`,
      [chart, aya, signal2],
    )

    await client.query('DELETE FROM bodha_grounding_matches WHERE target_kind=$1 AND target_id=$2', ['yoga_dosha_firing', '1'])
    expect(await integrity()).toBe(false)
    await client.query(
      `INSERT INTO bodha_grounding_matches VALUES ($1, $2, 'yoga_dosha_firing', '1', 'yukti', 'rule-1')`,
      [chart, aya],
    )

    await client.query(
      `INSERT INTO bodha_grounding_matches
       SELECT * FROM bodha_grounding_matches WHERE target_kind='msr_signal' LIMIT 1`,
    )
    expect(await integrity()).toBe(false)
    await client.query(`DELETE FROM bodha_grounding_matches a USING bodha_grounding_matches b
      WHERE a.ctid > b.ctid AND a.chart_id=b.chart_id AND a.ayanamsha_id=b.ayanamsha_id
        AND a.target_kind=b.target_kind AND a.target_id=b.target_id`)

    await client.query("UPDATE bodha_grounding_matches SET grounding_tier='invented' WHERE target_id=$1", [signal1])
    expect(await integrity()).toBe(false)
    await client.query("UPDATE bodha_grounding_matches SET grounding_tier='pratyaksa' WHERE target_id=$1", [signal1])

    await client.query("UPDATE bodha_grounding_matches SET grounding_tier='sruti', matched_rule_id=NULL WHERE target_id=$1", [signal1])
    expect(await integrity()).toBe(false)
    await client.query("UPDATE bodha_grounding_matches SET grounding_tier='pratyaksa' WHERE target_id=$1", [signal1])
  })

  it('fails a partial build but remains green when no chart has begun building', async () => {
    await client.query(
      `INSERT INTO bodha_msr_signals
       VALUES ('00000000-0000-0000-0000-000000000097', $1, $2)`,
      [unbuiltChart, aya],
    )
    await client.query(
      `INSERT INTO bodha_grounding_matches
       VALUES ($1, $2, 'msr_signal', '00000000-0000-0000-0000-000000000098', 'pratyaksa', NULL)`,
      [unbuiltChart, aya],
    )
    expect(await integrity()).toBe(false)

    await client.query('DELETE FROM bodha_grounding_matches')
    expect(await integrity()).toBe(true)
  })
})
