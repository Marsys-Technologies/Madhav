import fs from 'node:fs'
import path from 'node:path'
import { execFileSync } from 'node:child_process'
import { Client } from 'pg'
import { describe, expect, it } from 'vitest'

import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

const migrationPath = path.resolve(
  process.cwd(),
  'supabase/migrations/612_nirmana_l0_vastu_medical_integrity_contract.sql',
)
const migration = fs.existsSync(migrationPath) ? fs.readFileSync(migrationPath, 'utf8') : ''
const TEST_DATABASE_URL = process.env.NIRMANA_L0_VASTU_MEDICAL_TEST_DATABASE_URL

const HASHES = {
  vastuDirections: '1d18e307f87fa65932cb96ea4cff1dc8487262986ff5de4c969ab0b48497bb07',
  vastuRemedials: '0c9c3378e7f7ddb5205996d6f1d0a1b9ef5e47b7334f65d0225c5c88f2cbffe7',
  medicalMappings: 'b28082a5c41537272e5b7f31a0b8ccd3581fb5d7cf931d265ff20cc2c6879aea',
  nakshatraMedical: '52b968862b08590761b6fa6e3adef72e598965965f33694f4731e5d21c6e1ca9',
  signMedical: 'fc143d3109d4ffc20e1c78d952581d1b01ac7c4653f4a29ffc46396fa751769f',
} as const

const CONTRACTS = [
  {
    assetId: 'bg_sign_medical', sortOrder: 0, table: 'bg_sign_medical',
    countSql: 'SELECT COUNT(*) FROM bg_sign_medical', floor: 12, hasWriter: true,
  },
  {
    assetId: 'bg_vastu_directions', sortOrder: 56, table: 'bg_vastu_directions',
    countSql: 'SELECT (SELECT COUNT(*) FROM bg_vastu_directions) + (SELECT COUNT(*) FROM bg_vastu_direction_remedials) AS count',
    floor: 32, hasWriter: true,
  },
  {
    assetId: 'bg_medical_mappings', sortOrder: 64, table: 'bg_medical_mappings',
    countSql: 'SELECT COUNT(*) FROM bg_medical_mappings', floor: 21, hasWriter: true,
  },
  {
    assetId: 'bg_nakshatra_medical', sortOrder: 65, table: 'bg_nakshatra_medical',
    countSql: 'SELECT COUNT(*) FROM bg_nakshatra_medical', floor: 27, hasWriter: false,
  },
] as const

describe('migration 612 — vastu and medical producer integrity contracts', () => {
  it('is runner-owned, fail-closed, and aligned with the registry seed', () => {
    expect(migration).not.toBe('')
    expect(migration).toContain('migration 612 refuses unknown registry contract')
    expect(migration).not.toMatch(/^BEGIN;/m)
    expect(migration).not.toMatch(/^COMMIT;/m)
    for (const hash of Object.values(HASHES)) expect(migration).toContain(hash)

    for (const contract of CONTRACTS) {
      expect(ASSETS.find(asset => asset.asset_id === contract.assetId)).toMatchObject({
        sort_order: contract.sortOrder,
        target_table: contract.table,
        count_sql: contract.countSql,
        target_floor: contract.floor,
        depends_on: [],
      })
    }
  })
})

if (TEST_DATABASE_URL) {
  const parsed = new URL(TEST_DATABASE_URL)
  if (!['localhost', '127.0.0.1'].includes(parsed.hostname)
    || parsed.pathname !== '/nirmana_l0_vastu_medical_integrity_test') {
    throw new Error(
      'NIRMANA_L0_VASTU_MEDICAL_TEST_DATABASE_URL must point to the exact local '
      + 'nirmana_l0_vastu_medical_integrity_test database',
    )
  }
}

describe.skipIf(!TEST_DATABASE_URL)('migration 612 — real PostgreSQL behavior', () => {
  function runWriters(): void {
    execFileSync('python3', ['-c', [
      'import os, psycopg',
      'from brahmagyan.l0_vastu_directions import seed_vastu_directions',
      'from brahmagyan.l0_medical import seed_medical_mappings',
      'conn=psycopg.connect(os.environ["NIRMANA_L0_VASTU_MEDICAL_TEST_DATABASE_URL"])',
      'seed_vastu_directions(conn,autocommit=False)',
      'seed_medical_mappings(conn,build_id="migration-612-test",autocommit=False)',
      'conn.commit(); conn.close()',
    ].join('; ')], {
      cwd: path.resolve(process.cwd(), 'python-sidecar'),
      env: { ...process.env, NIRMANA_L0_VASTU_MEDICAL_TEST_DATABASE_URL: TEST_DATABASE_URL! },
      stdio: 'pipe',
    })
  }

  async function connectPrepared(): Promise<Client> {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    await client.query(`
      DROP TABLE IF EXISTS bg_vastu_direction_remedials, bg_vastu_directions,
        bg_medical_mappings, bg_nakshatra_medical, bg_sign_medical,
        asset_registry CASCADE;
      CREATE TABLE asset_registry (
        asset_id text PRIMARY KEY, layer text, sort_order integer, scope text,
        asset_kind text, catalog_status text, is_active boolean, has_writer boolean,
        target_table text, count_sql text, target_floor bigint, depends_on text[],
        integrity_check_sql text, english_description text, volume_explanation text
      );
      CREATE TABLE bg_vastu_directions (
        id serial PRIMARY KEY, direction text NOT NULL UNIQUE, direction_deg int,
        ruling_graha text NOT NULL, secondary_graha text, favorable_color text,
        element text, classical_citation text NOT NULL
      );
      CREATE TABLE bg_vastu_direction_remedials (
        id serial PRIMARY KEY, direction text NOT NULL REFERENCES bg_vastu_directions(direction),
        remedy_type text NOT NULL, remedy_description text NOT NULL,
        classical_citation text NOT NULL, UNIQUE(direction,remedy_type)
      );
      CREATE TABLE bg_medical_mappings (
        id serial PRIMARY KEY, graha text NOT NULL UNIQUE, dosha text[], dhatu text[],
        organ_systems text[], body_part text[], disease_tendency text[],
        classical_citation text NOT NULL
      );
      CREATE TABLE bg_nakshatra_medical (
        id serial PRIMARY KEY, nakshatra_name text NOT NULL UNIQUE,
        nakshatra_number int, body_part text NOT NULL, classical_citation text NOT NULL,
        dosha text
      );
      CREATE TABLE bg_sign_medical (
        sign_number int PRIMARY KEY, sign_name text NOT NULL UNIQUE,
        body_part text NOT NULL, organ_systems text[], element text NOT NULL,
        dosha text NOT NULL, classical_citation text NOT NULL
      );
    `)
    for (const contract of CONTRACTS) {
      await client.query(`
        INSERT INTO asset_registry
          (asset_id,layer,sort_order,scope,asset_kind,catalog_status,is_active,
           has_writer,target_table,count_sql,target_floor,depends_on,
           integrity_check_sql,english_description,volume_explanation)
        VALUES ($1,'brahmagyan',$2,'global','data','CURRENT',true,$3,
                $4,$5,$6,ARRAY[]::text[],NULL,$7,$8)
      `, [
        contract.assetId, contract.sortOrder, contract.hasWriter, contract.table,
        contract.countSql,
        contract.assetId === 'bg_medical_mappings' ? 9 : contract.floor,
        contract.assetId === 'bg_medical_mappings'
          ? 'Classical Ayurvedic graha → dosha/dhatu/organ/body-part mappings per BPHS Ch.18, Ashtanga Hridayam, Charaka Samhita. 9 grahas (Sun–Ketu). L0 static reference.'
          : 'fixture legacy description',
        contract.assetId === 'bg_medical_mappings'
          ? '9 rows = one row per classical graha (Sun through Ketu).'
          : 'fixture legacy explanation',
      ])
    }

    runWriters()
    return client
  }

  async function detectors(client: Client): Promise<Record<string, boolean>> {
    const contracts = await client.query<{ asset_id: string; integrity_check_sql: string }>(
      `SELECT asset_id,integrity_check_sql FROM asset_registry ORDER BY asset_id`,
    )
    const result: Record<string, boolean> = {}
    for (const contract of contracts.rows) {
      const observed = await client.query(contract.integrity_check_sql)
      result[contract.asset_id] = observed.rowCount === 1
        && Object.values(observed.rows[0])[0] === true
    }
    return result
  }

  it('installs, replays, and accepts exact deterministic writer output', async () => {
    const client = await connectPrepared()
    try {
      await client.query(migration)
      await client.query(migration)
      expect(await detectors(client)).toEqual({
        bg_medical_mappings: true,
        bg_nakshatra_medical: true,
        bg_sign_medical: true,
        bg_vastu_directions: true,
      })
      const medical = await client.query(
        `SELECT target_floor,english_description,volume_explanation FROM asset_registry WHERE asset_id='bg_medical_mappings'`,
      )
      expect(medical.rows[0]).toEqual({
        target_floor: '21',
        english_description: 'Classical Ayurvedic Jyotish mappings per BPHS Ch.18, Ashtanga Hridayam, and Charaka Samhita: 9 grahas, 6 planetary combinations, and 6 dignity modifiers. L0 static reference.',
        volume_explanation: '21 deterministic medical mapping rows: 9 classical grahas + 6 planetary combinations + 6 dignity modifiers.',
      })
    } finally {
      await client.end()
    }
  })

  it('fires on a semantic mutation in every owned table', async () => {
    const client = await connectPrepared()
    try {
      await client.query(migration)
      const corruptions = [
        ["UPDATE bg_vastu_directions SET element='drift' WHERE direction='North'", 'bg_vastu_directions'],
        ["UPDATE bg_vastu_direction_remedials SET remedy_description='drift' WHERE id=(SELECT min(id) FROM bg_vastu_direction_remedials)", 'bg_vastu_directions'],
        ["UPDATE bg_medical_mappings SET classical_citation='drift' WHERE graha='Sun'", 'bg_medical_mappings'],
        ["UPDATE bg_nakshatra_medical SET body_part='drift' WHERE nakshatra_number=1", 'bg_nakshatra_medical'],
        ["UPDATE bg_sign_medical SET body_part='drift' WHERE sign_number=1", 'bg_sign_medical'],
      ] as const
      await client.query('BEGIN')
      for (const [sql, assetId] of corruptions) {
        await client.query('SAVEPOINT corruption')
        await client.query(sql)
        expect((await detectors(client))[assetId]).toBe(false)
        if (assetId === 'bg_nakshatra_medical' || assetId === 'bg_sign_medical') {
          expect((await detectors(client)).bg_medical_mappings).toBe(false)
        }
        await client.query('ROLLBACK TO SAVEPOINT corruption')
      }
      await client.query('ROLLBACK')
    } finally {
      await client.end()
    }
  })

  it('fires on missing or additional rows', async () => {
    const client = await connectPrepared()
    try {
      await client.query(migration)
      await client.query(`DELETE FROM bg_vastu_direction_remedials WHERE id=(SELECT min(id) FROM bg_vastu_direction_remedials)`)
      expect((await detectors(client)).bg_vastu_directions).toBe(false)

      await client.query(`INSERT INTO bg_sign_medical VALUES (13,'Drift','drift',ARRAY['drift'],'fire','pitta','drift')`)
      expect((await detectors(client)).bg_sign_medical).toBe(false)
      expect((await detectors(client)).bg_medical_mappings).toBe(false)
    } finally {
      await client.end()
    }
  })

  it('repairs drifted Vastu remedial content on writer replay', async () => {
    const client = await connectPrepared()
    try {
      await client.query(migration)
      await client.query(`UPDATE bg_vastu_direction_remedials
                          SET remedy_description='drift',classical_citation='drift'
                          WHERE direction='East' AND remedy_type='color'`)
      expect((await detectors(client)).bg_vastu_directions).toBe(false)
      runWriters()
      expect((await detectors(client)).bg_vastu_directions).toBe(true)
    } finally {
      await client.end()
    }
  })

  it('rejects registry drift atomically without changing the medical floor', async () => {
    const client = await connectPrepared()
    try {
      await client.query(`UPDATE asset_registry SET target_floor=1 WHERE asset_id='bg_vastu_directions'`)
      await expect(client.query(migration)).rejects.toThrow(
        'migration 612 refuses unknown registry contract',
      )
      const observed = await client.query(
        `SELECT count(*) FILTER (WHERE integrity_check_sql IS NOT NULL)::int AS installed,
                max(target_floor) FILTER (WHERE asset_id='bg_medical_mappings') AS medical_floor
         FROM asset_registry`,
      )
      expect(observed.rows[0]).toEqual({ installed: 0, medical_floor: '9' })
    } finally {
      await client.end()
    }
  })
})
