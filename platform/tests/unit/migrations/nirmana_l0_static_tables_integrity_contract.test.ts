import fs from 'node:fs'
import path from 'node:path'
import { execFileSync } from 'node:child_process'
import { Client } from 'pg'
import { describe, expect, it } from 'vitest'

import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

const migrationPath = path.resolve(
  process.cwd(),
  'supabase/migrations/611_nirmana_l0_static_tables_integrity_contract.sql',
)
const migration = fs.existsSync(migrationPath) ? fs.readFileSync(migrationPath, 'utf8') : ''
const TEST_DATABASE_URL = process.env.NIRMANA_L0_STATIC_INTEGRITY_TEST_DATABASE_URL

const CONTRACTS = [
  {
    assetId: 'bg_kota_chakra_rings', sortOrder: 72, table: 'bg_kota_chakra_rings',
    countSql: 'SELECT COUNT(*) FROM bg_kota_chakra_rings', floor: 27,
    digest: 'ec9c877dd2c143d4deb7a74dc490ced4761a90b61e0e23e7aa7589a40cc91bf7',
  },
  {
    assetId: 'bg_vedha_malefic_scale', sortOrder: 74, table: 'bg_vedha_malefic_scale',
    countSql: 'SELECT COUNT(*) FROM bg_vedha_malefic_scale', floor: 5,
    digest: '9ee5d8436059fa96d5fa60d8be6d0cc25cc8865e1013ef1bed8ff6810342ff1c',
  },
  {
    assetId: 'bg_phaladeepika_latta', sortOrder: 75, table: 'bg_phaladeepika_latta',
    countSql: 'SELECT COUNT(*) FROM bg_phaladeepika_latta', floor: 8,
    digest: '11fdcce56802e2fd5aab056b426cb6eb2a75cb6c2b1fd705df52113b44010e88',
  },
] as const

describe('migration 611 — closed L0 static-table integrity contracts', () => {
  it('is runner-owned, fail-closed, and aligned with the registry seed', () => {
    expect(migration).not.toBe('')
    expect(migration).toContain('migration 611 refuses unknown registry contract')
    expect(migration).not.toMatch(/^BEGIN;/m)
    expect(migration).not.toMatch(/^COMMIT;/m)

    for (const contract of CONTRACTS) {
      const asset = ASSETS.find(candidate => candidate.asset_id === contract.assetId)
      expect(asset).toMatchObject({
        sort_order: contract.sortOrder,
        target_table: contract.table,
        count_sql: contract.countSql,
        target_floor: contract.floor,
        depends_on: [],
      })
      expect(migration).toContain(contract.digest)
    }
  })
})

if (TEST_DATABASE_URL) {
  const parsed = new URL(TEST_DATABASE_URL)
  if (!['localhost', '127.0.0.1'].includes(parsed.hostname)
    || parsed.pathname !== '/nirmana_l0_static_integrity_test') {
    throw new Error(
      'NIRMANA_L0_STATIC_INTEGRITY_TEST_DATABASE_URL must point to the exact local '
      + 'nirmana_l0_static_integrity_test database',
    )
  }
}

describe.skipIf(!TEST_DATABASE_URL)('migration 611 — real PostgreSQL behavior', () => {
  async function connectPrepared(): Promise<Client> {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    await client.query(`
      DROP TABLE IF EXISTS bg_kota_chakra_rings, bg_vedha_malefic_scale,
        bg_phaladeepika_latta, asset_registry CASCADE;
      CREATE TABLE asset_registry (
        asset_id text PRIMARY KEY, layer text, sort_order integer, scope text,
        asset_kind text, catalog_status text, is_active boolean, has_writer boolean,
        target_table text, count_sql text, target_floor bigint, depends_on text[],
        integrity_check_sql text
      );
      CREATE TABLE bg_kota_chakra_rings (
        table_version text NOT NULL, ring_position smallint NOT NULL,
        ring_name text NOT NULL, ring_index smallint NOT NULL,
        dvara_assignment text, citation text NOT NULL, corpus_status text NOT NULL,
        ratified_by text, created_at timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY (table_version, ring_position)
      );
      CREATE TABLE bg_vedha_malefic_scale (
        table_version text NOT NULL, malefic_count smallint NOT NULL,
        effect_grade text NOT NULL, effect_description text NOT NULL,
        source_citation text NOT NULL, verse_ref text NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY (table_version, malefic_count)
      );
      CREATE TABLE bg_phaladeepika_latta (
        table_version text NOT NULL, graha text NOT NULL,
        count_from_graha smallint NOT NULL, direction text NOT NULL,
        effect_description text, affliction_condition text NOT NULL,
        source_citation text NOT NULL, verse_ref text NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY (table_version, graha)
      );
    `)
    for (const contract of CONTRACTS) {
      await client.query(`
        INSERT INTO asset_registry
          (asset_id,layer,sort_order,scope,asset_kind,catalog_status,is_active,
           has_writer,target_table,count_sql,target_floor,depends_on,integrity_check_sql)
        VALUES ($1,'brahmagyan',$2,'global','data','CURRENT',true,true,
                $3,$4,$5,ARRAY[]::text[],NULL)
      `, [contract.assetId, contract.sortOrder, contract.table, contract.countSql, contract.floor])
    }

    execFileSync('python3', ['-c', [
      'import os, psycopg',
      'from brahmagyan.l0_kota_chakra_rings import seed_kota_chakra_rings',
      'from brahmagyan.l0_phaladeepika_vedha import seed_vedha_malefic_scale, seed_phaladeepika_latta',
      'conn=psycopg.connect(os.environ["NIRMANA_L0_STATIC_INTEGRITY_TEST_DATABASE_URL"])',
      'seed_kota_chakra_rings(conn,autocommit=False)',
      'seed_vedha_malefic_scale(conn,autocommit=False)',
      'seed_phaladeepika_latta(conn,autocommit=False)',
      'conn.commit(); conn.close()',
    ].join('; ')], {
      cwd: path.resolve(process.cwd(), 'python-sidecar'),
      env: { ...process.env, NIRMANA_L0_STATIC_INTEGRITY_TEST_DATABASE_URL: TEST_DATABASE_URL! },
      stdio: 'pipe',
    })
    return client
  }

  async function detectors(client: Client): Promise<Record<string, boolean>> {
    const contracts = await client.query<{ asset_id: string; integrity_check_sql: string }>(
      `SELECT asset_id,integrity_check_sql FROM asset_registry ORDER BY asset_id`,
    )
    const observed: Record<string, boolean> = {}
    for (const contract of contracts.rows) {
      const result = await client.query(contract.integrity_check_sql)
      observed[contract.asset_id] = result.rowCount === 1
        && Object.values(result.rows[0])[0] === true
    }
    return observed
  }

  it('installs, replays, and accepts the exact deterministic writer output', async () => {
    const client = await connectPrepared()
    try {
      await client.query(migration)
      await client.query(migration)
      expect(await detectors(client)).toEqual({
        bg_kota_chakra_rings: true,
        bg_phaladeepika_latta: true,
        bg_vedha_malefic_scale: true,
      })
    } finally {
      await client.end()
    }
  })

  it('fires on count-preserving semantic mutations for every table', async () => {
    const client = await connectPrepared()
    try {
      await client.query(migration)
      const corruptions = [
        ["UPDATE bg_kota_chakra_rings SET ring_name='drift' WHERE ring_position=1", 'bg_kota_chakra_rings'],
        ["UPDATE bg_vedha_malefic_scale SET effect_grade='drift' WHERE malefic_count=1", 'bg_vedha_malefic_scale'],
        ["UPDATE bg_phaladeepika_latta SET effect_description='drift' WHERE graha='Sun'", 'bg_phaladeepika_latta'],
      ] as const
      await client.query('BEGIN')
      for (const [sql, assetId] of corruptions) {
        await client.query('SAVEPOINT corruption')
        await client.query(sql)
        expect((await detectors(client))[assetId]).toBe(false)
        await client.query('ROLLBACK TO SAVEPOINT corruption')
      }
      await client.query('ROLLBACK')
    } finally {
      await client.end()
    }
  })

  it('fires when a required row is removed or an unreviewed version is added', async () => {
    const client = await connectPrepared()
    try {
      await client.query(migration)
      await client.query('BEGIN')
      await client.query('DELETE FROM bg_kota_chakra_rings WHERE ring_position=27')
      expect((await detectors(client)).bg_kota_chakra_rings).toBe(false)
      await client.query('ROLLBACK')

      await client.query('BEGIN')
      await client.query(`
        INSERT INTO bg_vedha_malefic_scale
        SELECT 'phaladeepika_vedha_v02',malefic_count,effect_grade,effect_description,
               source_citation,verse_ref,now()
        FROM bg_vedha_malefic_scale WHERE malefic_count=1
      `)
      expect((await detectors(client)).bg_vedha_malefic_scale).toBe(false)
      await client.query('ROLLBACK')
    } finally {
      await client.end()
    }
  })

  it('rejects registry drift atomically without installing any detector', async () => {
    const client = await connectPrepared()
    try {
      await client.query(`UPDATE asset_registry SET target_floor=1 WHERE asset_id='bg_kota_chakra_rings'`)
      await expect(client.query(migration)).rejects.toThrow(
        'migration 611 refuses unknown registry contract',
      )
      const installed = await client.query(
        `SELECT count(*)::int AS n FROM asset_registry WHERE integrity_check_sql IS NOT NULL`,
      )
      expect(installed.rows[0].n).toBe(0)
    } finally {
      await client.end()
    }
  })
})
