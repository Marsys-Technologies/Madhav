import fs from 'node:fs'
import path from 'node:path'
import { execFileSync } from 'node:child_process'
import { Client } from 'pg'
import { describe, expect, it } from 'vitest'

import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

const migrationPath = path.resolve(
  process.cwd(),
  'supabase/migrations/613_nirmana_l0_transit_integrity_contract.sql',
)
const migration = fs.existsSync(migrationPath) ? fs.readFileSync(migrationPath, 'utf8') : ''
const TEST_DATABASE_URL = process.env.NIRMANA_L0_TRANSIT_TEST_DATABASE_URL

const HASHES = {
  engine: 'e2dafc84d7fef9b8a05ad01b98b036686e8ec0af9694a4d43ac4b2b8c425797b',
  rules: '13616890d782a47cf667a4b1d3c52d2be08408a80f647d0e4aed4fc38cae3e54',
  moorti: 'b411c02abb7fec89c971353190f1ebe117a31a85e1bba06aeadc6509d0256450',
} as const

describe('migration 613 — transit producer integrity contract', () => {
  it('is runner-owned, fail-closed, and aligned with the registry seed', () => {
    expect(migration).not.toBe('')
    expect(migration).toContain('migration 613 refuses unknown registry contract')
    expect(migration).not.toMatch(/^BEGIN;/m)
    expect(migration).not.toMatch(/^COMMIT;/m)
    for (const hash of Object.values(HASHES)) expect(migration).toContain(hash)
    expect(ASSETS.find(asset => asset.asset_id === 'bg_transit_engine')).toMatchObject({
      sort_order: 61,
      target_table: 'bg_transit_engine',
      count_sql: 'SELECT COUNT(*) FROM bg_transit_engine',
      target_floor: 9,
      depends_on: [],
    })
    expect(ASSETS.find(asset => asset.asset_id === 'bg_transit_rules')).toMatchObject({
      sort_order: 62,
      target_table: 'bg_transit_rules',
      count_sql: 'SELECT COUNT(*) FROM bg_transit_rules',
      target_floor: 75,
      depends_on: [],
    })
  })
})

if (TEST_DATABASE_URL) {
  const parsed = new URL(TEST_DATABASE_URL)
  if (!['localhost', '127.0.0.1'].includes(parsed.hostname)
    || parsed.pathname !== '/nirmana_l0_transit_integrity_test') {
    throw new Error(
      'NIRMANA_L0_TRANSIT_TEST_DATABASE_URL must point to the exact local '
      + 'nirmana_l0_transit_integrity_test database',
    )
  }
}

describe.skipIf(!TEST_DATABASE_URL)('migration 613 — real PostgreSQL behavior', () => {
  const canonicalDescription = '75 classical transit rules: 42 favourable, 26 unfavourable, and 7 double-transit rules from BPHS Ch.29, Phaladeepika Ch.26, Saravali, and Jataka Parijata.'
  const canonicalExplanation = '75 rows = 68 writer-owned Gochara rules (42 favourable + 26 unfavourable) plus 7 preserved migration-owned Jupiter–Saturn double-transit rules.'

  function runWriter(): void {
    execFileSync('python3', ['-c', [
      'import os, psycopg',
      'from psycopg.rows import dict_row',
      'from brahmagyan.l0_transit import seed_transit_rules',
      'conn=psycopg.connect(os.environ["NIRMANA_L0_TRANSIT_TEST_DATABASE_URL"],row_factory=dict_row)',
      'seed_transit_rules(conn)',
      'conn.commit(); conn.close()',
    ].join('; ')], {
      cwd: path.resolve(process.cwd(), 'python-sidecar'),
      env: { ...process.env, NIRMANA_L0_TRANSIT_TEST_DATABASE_URL: TEST_DATABASE_URL! },
      stdio: 'pipe',
    })
  }

  async function connectPrepared(): Promise<Client> {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    await client.query(`
      DROP TABLE IF EXISTS bg_transit_moorti,bg_transit_rules,bg_transit_engine,asset_registry CASCADE;
      CREATE TABLE asset_registry (
        asset_id text PRIMARY KEY, layer text, sort_order integer, scope text,
        asset_kind text, catalog_status text, is_active boolean, has_writer boolean,
        target_table text, count_sql text, target_floor bigint, depends_on text[],
        integrity_check_sql text, english_description text, volume_explanation text
      );
      CREATE TABLE bg_transit_engine (
        id serial PRIMARY KEY, graha text NOT NULL UNIQUE,
        avg_daily_motion_deg numeric NOT NULL, zodiac_period_days numeric NOT NULL,
        sign_residence_days numeric NOT NULL, classical_citation text NOT NULL
      );
      CREATE TABLE bg_transit_rules (
        id serial PRIMARY KEY, rule_type text NOT NULL, graha text NOT NULL,
        primary_house integer NOT NULL, vedha_house integer, phala text NOT NULL,
        classical_citation text NOT NULL, rule_notes text,
        UNIQUE(graha,rule_type,primary_house)
      );
      CREATE TABLE bg_transit_moorti (
        nakshatra_offset integer PRIMARY KEY, moorti_name text NOT NULL,
        quality_tier integer NOT NULL, phala_brief text NOT NULL,
        classical_citation text NOT NULL, rule_notes text
      );
      INSERT INTO asset_registry
        (asset_id,layer,sort_order,scope,asset_kind,catalog_status,is_active,
         has_writer,target_table,count_sql,target_floor,depends_on,
         integrity_check_sql,english_description,volume_explanation)
      VALUES
        ('bg_transit_engine','brahmagyan',61,'global','data','CURRENT',true,false,
         'bg_transit_engine','SELECT COUNT(*) FROM bg_transit_engine',9,ARRAY[]::text[],NULL,
         'L0 average graha motion parameters — daily motion, zodiac period, sign residence. Source: BPHS Ch.22.',
         '9 rows = 7 classical grahas + Rahu + Ketu motion parameters.'),
        ('bg_transit_rules','brahmagyan',62,'global','data','CURRENT',true,true,
         'bg_transit_rules','SELECT COUNT(*) FROM bg_transit_rules',50,ARRAY[]::text[],NULL,
         'Classical transit rules (favourable/unfavourable/vedha houses) from BPHS Ch.29 and Phaladeepika Ch.26.',
         '50 classical gochara transit rules per actual build count (41 base + 9 Venus gochara phala rows added Phase B).');
      INSERT INTO bg_transit_rules
        (rule_type,graha,primary_house,vedha_house,phala,classical_citation,rule_notes)
      VALUES
        ('double_transit','Jupiter',2,NULL,'Jupiter + Saturn in 2H simultaneously: wealth and stability gains amplified; Dhana yoga catalyst.','Phaladeepika ch.26 §double-gochara; Saravali ch.28','Applies only when BOTH Jupiter and Saturn transit 2H from natal Moon within 30° window.'),
        ('double_transit','Jupiter',5,NULL,'Jupiter + Saturn in 5H: putra karaka + karma lord in progeny house — children-related events, creative fruition.','Phaladeepika ch.26 §double-gochara','Saturn alone in 5H is unfavourable; Jupiter co-presence mitigates and transforms.'),
        ('double_transit','Jupiter',7,NULL,'Jupiter + Saturn in 7H: relationship events crystallise; partnerships formalised or resolved.','Phaladeepika ch.26 §double-gochara; BPHS ch.29',NULL),
        ('double_transit','Jupiter',9,NULL,'Jupiter + Saturn in 9H: dharmic milestones; pilgrimage, guru connection, institutional advancement.','Phaladeepika ch.26 §double-gochara','Most auspicious double-transit combination per classical consensus.'),
        ('double_transit','Jupiter',11,NULL,'Jupiter + Saturn in 11H: significant gain period — labha amplified by both benefic + discipline.','Phaladeepika ch.26 §double-gochara; Jataka Parijata',NULL),
        ('double_transit','Saturn',4,NULL,'Jupiter + Saturn in 4H: domestic disruption + karmic pressure; home/vehicle events likely.','Phaladeepika ch.26 §double-gochara','Jupiter mitigates isolation but Saturn delays resolution.'),
        ('double_transit','Saturn',8,NULL,'Jupiter + Saturn in 8H: transformation event; inheritance, hidden matters, health threshold.','Phaladeepika ch.26 §double-gochara; BPHS ch.29 §8H gochara','Rare and intense. Jupiter here expands the 8H matters rather than protecting.');
    `)
    runWriter()
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

  it('installs, replays, and accepts the exact composite producer output', async () => {
    const client = await connectPrepared()
    try {
      await client.query(migration)
      await client.query(migration)
      expect(await detectors(client)).toEqual({ bg_transit_engine: true, bg_transit_rules: true })
      const rules = await client.query(
        `SELECT target_floor,english_description,volume_explanation
         FROM asset_registry WHERE asset_id='bg_transit_rules'`,
      )
      expect(rules.rows[0]).toEqual({
        target_floor: '75',
        english_description: canonicalDescription,
        volume_explanation: canonicalExplanation,
      })
    } finally {
      await client.end()
    }
  })

  it('fires on semantic drift in every producer component', async () => {
    const client = await connectPrepared()
    try {
      await client.query(migration)
      const corruptions = [
        ["UPDATE bg_transit_engine SET classical_citation='drift' WHERE graha='sun'", 'bg_transit_engine'],
        ["UPDATE bg_transit_rules SET phala='drift' WHERE graha='sun' AND rule_type='favourable' AND primary_house=3", 'bg_transit_rules'],
        ["UPDATE bg_transit_moorti SET phala_brief='drift' WHERE nakshatra_offset=1", 'bg_transit_rules'],
        ["UPDATE bg_transit_rules SET phala='drift' WHERE rule_type='double_transit' AND graha='Jupiter' AND primary_house=2", 'bg_transit_rules'],
      ] as const
      await client.query('BEGIN')
      for (const [sql, assetId] of corruptions) {
        await client.query('SAVEPOINT corruption')
        await client.query(sql)
        expect((await detectors(client))[assetId]).toBe(false)
        if (assetId === 'bg_transit_engine') expect((await detectors(client)).bg_transit_rules).toBe(false)
        await client.query('ROLLBACK TO SAVEPOINT corruption')
      }
      await client.query('ROLLBACK')
    } finally {
      await client.end()
    }
  })

  it('rejects registry drift atomically without changing the rules floor', async () => {
    const client = await connectPrepared()
    try {
      await client.query(`UPDATE asset_registry SET target_floor=1 WHERE asset_id='bg_transit_engine'`)
      await expect(client.query(migration)).rejects.toThrow(
        'migration 613 refuses unknown registry contract',
      )
      const observed = await client.query(
        `SELECT count(*) FILTER (WHERE integrity_check_sql IS NOT NULL)::int AS installed,
                max(target_floor) FILTER (WHERE asset_id='bg_transit_rules') AS rules_floor
         FROM asset_registry`,
      )
      expect(observed.rows[0]).toEqual({ installed: 0, rules_floor: '50' })
    } finally {
      await client.end()
    }
  })
})
