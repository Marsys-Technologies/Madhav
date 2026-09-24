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

// L0 repair items 1-3 re-cited 35 rows, corrected three Venus vedha pairs and
// INSERTED the missing Mercury 8th->1st pair, moving the table from 75 rows
// (42 favourable) to 76 (43 favourable). Migration 613 pins the pre-repair shape
// and content and therefore now refuses it — by design. Migration 1078 is the
// governed reseal; the DB tests apply 613 THEN 1078, the real deployed order.
const resealPath = path.resolve(
  process.cwd(),
  'supabase/migrations/1078_nirmana_l0_transit_rules_integrity_reseal.sql',
)
const reseal = fs.existsSync(resealPath) ? fs.readFileSync(resealPath, 'utf8') : ''

// Migration 1078's description dropped BPHS Ch.29 from the source list, but 19 rows
// still carry it (they sit outside item 1's verified predicate). 1079 corrects that
// prose to a measured census. Applied third, mirroring production.
const truthfulPath = path.resolve(
  process.cwd(),
  'supabase/migrations/1079_nirmana_l0_transit_rules_description_truthfulness.sql',
)
const truthful = fs.existsSync(truthfulPath) ? fs.readFileSync(truthfulPath, 'utf8') : ''

const HASHES = {
  engine: 'e2dafc84d7fef9b8a05ad01b98b036686e8ec0af9694a4d43ac4b2b8c425797b',
  rules: '13616890d782a47cf667a4b1d3c52d2be08408a80f647d0e4aed4fc38cae3e54',
  moorti: 'b411c02abb7fec89c971353190f1ebe117a31a85e1bba06aeadc6509d0256450',
} as const

// bg_transit_engine and bg_transit_moorti were NOT touched by the repair; their
// pinned hashes carry over byte-identical into the reseal, which is what proves
// the repair's blast radius really was confined to bg_transit_rules.
const RESEALED_RULES_HASH = '1dbdd265cf0e04edd26aebde054f34d9034be38bfabc8102085b0127196a598d'

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
      // 76 after L0 repair item 2's INSERT; the seed and migration 1078 must agree
      // or a fresh install and a migrated install would disagree on the floor.
      target_floor: 76,
      depends_on: [],
    })
  })

  it('carries a governed reseal for the rows L0 repair items 1-3 changed', () => {
    expect(reseal).not.toBe('')
    expect(reseal).toContain('migration 1078 refuses')
    // the new content hash and the new shape both appear...
    expect(reseal).toContain(RESEALED_RULES_HASH)
    expect(reseal).toContain('count(*) = 76 FROM bg_transit_rules')
    // ...and the superseded ones are named in the guard, so 1078 can only land on
    // top of exactly 613's contract, never onto an unknown one.
    expect(reseal).toContain(HASHES.rules)
    expect(migration).not.toContain(RESEALED_RULES_HASH)
    // untouched components carry over unchanged — the proof of blast radius
    expect(reseal).toContain(HASHES.engine)
    expect(reseal).toContain(HASHES.moorti)
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
  // what migration 613 installs (the pre-repair shape), asserted so the reseal is
  // proven to land on exactly this state and nothing else
  const canonicalDescription = '75 classical transit rules: 42 favourable, 26 unfavourable, and 7 double-transit rules from BPHS Ch.29, Phaladeepika Ch.26, Saravali, and Jataka Parijata.'
  const canonicalExplanation = '75 rows = 68 writer-owned Gochara rules (42 favourable + 26 unfavourable) plus 7 preserved migration-owned Jupiter–Saturn double-transit rules.'
  // what migration 1078 leaves behind (the post-repair shape, before 1079's correction)
  const resealedDescription = '76 classical transit rules: 43 favourable, 26 unfavourable, and 7 double-transit rules from Phaladeepika Adh. XXVI (page-anchored) and Saravali/Jataka Parijata (double-transit). L0 repair 2026-09: re-cited off the refuted "BPHS Ch.29", corrected 3 Venus vedha pairs, inserted the missing Mercury 8th-house pair, marked 6 Rahu/Ketu rows honestly unsourced.'
  // what migration 1079 leaves behind (the measured census)
  const truthfulDescription = '76 classical transit rules: 43 favourable, 26 unfavourable, 7 double-transit. Citation state after the 2026-09 L0 repair, measured not asserted: 36 favourable-with-vedha rows carry page-anchored Phaladipika Adh. XXVI citations (PG322:C1/PG323:C1); 6 Rahu/Ketu favourable-with-vedha rows are declared UNSOURCED (the served corpus carries no house-transit vedha doctrine for the nodes); 19 rows (18 unfavourable + 1 favourable with no vedha pair) STILL carry the refuted "BPHS Ch.29" — they lie outside the repair\'s row-by-row verified predicate and were deliberately not re-cited on an unverified basis; the remaining 15 cite Phaladeepika Ch.26, Adh. XXVI slokas 2/8/21, Saravali or Jataka Parijata.'
  const resealedExplanation = '76 rows = 69 writer-owned Gochara rules (43 favourable + 26 unfavourable) plus 7 preserved migration-owned Jupiter–Saturn double-transit rules. The 69th writer-owned row is the Mercury 8th-house-transit/1st-house-vedha pair L0 repair item 2 inserted (KSHETRA_L0_VEDHA_ROW_FIXES_v1_0.md Sec.3) — present in the text, absent from every prior build.'

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
      // 613 alone now refuses bg_transit_rules — the repair changed the shape and
      // content it pins. bg_transit_engine is unaffected, which is the point.
      expect(await detectors(client)).toEqual({ bg_transit_engine: true, bg_transit_rules: false })
      const preReseal = await client.query(
        `SELECT target_floor,english_description,volume_explanation
         FROM asset_registry WHERE asset_id='bg_transit_rules'`,
      )
      expect(preReseal.rows[0]).toEqual({
        target_floor: '75',
        english_description: canonicalDescription,
        volume_explanation: canonicalExplanation,
      })
      // applied once: 1078's guard pins the predecessor contract by value, so a
      // second application correctly refuses (verified against production).
      await client.query(reseal)
      expect(await detectors(client)).toEqual({ bg_transit_engine: true, bg_transit_rules: true })
      const rules = await client.query(
        `SELECT target_floor,english_description,volume_explanation
         FROM asset_registry WHERE asset_id='bg_transit_rules'`,
      )
      expect(rules.rows[0]).toEqual({
        target_floor: '76',
        english_description: resealedDescription,
        volume_explanation: resealedExplanation,
      })
      // 1079 replaces 1078's prose with a census that must agree with the table
      await client.query(truthful)
      const corrected = await client.query(
        `SELECT english_description FROM asset_registry WHERE asset_id='bg_transit_rules'`,
      )
      expect(corrected.rows[0].english_description).toEqual(truthfulDescription)
      // the description's own numbers are checkable against the rows, so this
      // assertion fails if the prose and the data ever diverge again
      const census = await client.query<{ bphs: string; unsourced: string; anchored: string }>(`
        SELECT count(*) FILTER (WHERE classical_citation = 'BPHS Ch.29 (Gochara Phala — Transit Results)')::text AS bphs,
               count(*) FILTER (WHERE classical_citation LIKE 'UNSOURCED%')::text AS unsourced,
               count(*) FILTER (WHERE classical_citation LIKE 'Phaladipika Adh. XXVI, Sloka%')::text AS anchored
        FROM bg_transit_rules
      `)
      expect(census.rows[0]).toEqual({ bphs: '19', unsourced: '6', anchored: '36' })
      expect(corrected.rows[0].english_description).toContain('19 rows')
      expect(corrected.rows[0].english_description).toContain('36 favourable-with-vedha')
    } finally {
      await client.end()
    }
  })

  it('fires on semantic drift in every producer component', async () => {
    const client = await connectPrepared()
    try {
      await client.query(migration)
      // reseal first: without it bg_transit_rules' detector is already false for a
      // legitimate reason and every assertion below would pass vacuously.
      await client.query(reseal)
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
