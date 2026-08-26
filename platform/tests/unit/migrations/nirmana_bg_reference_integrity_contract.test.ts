import fs from 'node:fs'
import path from 'node:path'
import { execFileSync } from 'node:child_process'
import { Client } from 'pg'
import { describe, expect, it } from 'vitest'

import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

const migrationPath = path.resolve(
  process.cwd(),
  'supabase/migrations/607_nirmana_bg_reference_integrity_contract.sql',
)
const migration = fs.existsSync(migrationPath) ? fs.readFileSync(migrationPath, 'utf8') : ''
const ws2Schema = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/ws2_l0_reference.sql'),
  'utf8',
)
const phaseAlphaOwnedSchema = fs.readFileSync(
  path.resolve(process.cwd(), 'supabase/migrations/178_l0_phase_alpha_reference_tables.sql'),
  'utf8',
).split('-- Pointer tables')[0].replace(/^BEGIN;\s*$/m, '')

describe('migration 607 — bg_reference integrity contract', () => {
  it('installs a runner-owned executable contract aligned with the replay seed', () => {
    const reference = ASSETS.find(asset => asset.asset_id === 'bg_reference')
    expect(reference?.depends_on).toEqual(['bg_ontology'])
    expect(reference?.target_floor).toBe(1242)
    expect(migration).toContain("migration 607 refuses unknown bg_reference registry contract")
    expect(migration).toContain('integrity_check_sql = reference_check')
    expect(migration).not.toMatch(/^BEGIN;/m)
    expect(migration).not.toMatch(/^COMMIT;/m)
  })
})

const TEST_DATABASE_URL = process.env.NIRMANA_BG_REFERENCE_INTEGRITY_TEST_DATABASE_URL

if (TEST_DATABASE_URL) {
  const parsed = new URL(TEST_DATABASE_URL)
  if (!['localhost', '127.0.0.1'].includes(parsed.hostname)
    || parsed.pathname !== '/nirmana_bg_reference_integrity_test') {
    throw new Error(
      'NIRMANA_BG_REFERENCE_INTEGRITY_TEST_DATABASE_URL must point to the exact local '
      + 'nirmana_bg_reference_integrity_test database',
    )
  }
}

describe.skipIf(!TEST_DATABASE_URL)('migration 607 — real Postgres behavior', () => {
  async function connectPrepared(): Promise<Client> {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    await client.query(`
      DROP TABLE IF EXISTS
        asset_registry, brahma_ontology, reference_planets,
        reference_nakshatras, reference_signs, reference_aspects,
        reference_vargas, reference_houses, reference_strength_systems,
        reference_karakas, reference_upagrahas, reference_constants,
        reference_topic_tags, reference_glossary
      CASCADE;
    `)
    await client.query(ws2Schema)
    await client.query(phaseAlphaOwnedSchema)
    await client.query(`
      CREATE TABLE brahma_ontology (canonical_id text PRIMARY KEY);
      INSERT INTO brahma_ontology VALUES ('source-authority-present');

      CREATE TABLE asset_registry (
        asset_id text PRIMARY KEY,
        layer text,
        sort_order integer,
        scope text,
        asset_kind text,
        catalog_status text,
        is_active boolean,
        has_writer boolean,
        target_table text,
        count_sql text,
        target_floor bigint,
        volume_explanation text,
        depends_on text[],
        integrity_check_sql text
      );
      INSERT INTO asset_registry VALUES (
        'bg_reference','brahmagyan',2,'global','data','CURRENT',true,true,
        'reference_planets',
        'SELECT (SELECT count(*) FROM reference_planets) + (SELECT count(*) FROM reference_signs) + (SELECT count(*) FROM reference_aspects) + (SELECT count(*) FROM reference_vargas) + (SELECT count(*) FROM reference_houses) + (SELECT count(*) FROM reference_strength_systems) + (SELECT count(*) FROM reference_karakas) + (SELECT count(*) FROM reference_upagrahas) + (SELECT count(*) FROM reference_constants) + (SELECT count(*) FROM reference_topic_tags) + (SELECT count(*) FROM reference_glossary) AS count',
        1242,
        '1,242 achieved rows across the 11 tables owned by bg_reference, as measured in the BA full-asset audit after migration 371 removed cross-asset double-counting. reference_yogas, reference_doshas, and reference_dasha_systems are owned by their dedicated assets; deprecated reference_nakshatras is excluded.',
        ARRAY['bg_ontology']::text[],NULL
      );
    `)
    return client
  }

  async function installHealthyFixtures(client: Client): Promise<void> {
    execFileSync('python3', ['-c', [
      'import os, psycopg',
      'from brahmagyan.l0_reference import seed_reference',
      'conn = psycopg.connect(os.environ["NIRMANA_BG_REFERENCE_INTEGRITY_TEST_DATABASE_URL"])',
      'seed_reference(conn)',
      'conn.close()',
    ].join('; ')], {
      cwd: path.resolve(process.cwd(), 'python-sidecar'),
      env: { ...process.env, NIRMANA_BG_REFERENCE_INTEGRITY_TEST_DATABASE_URL: TEST_DATABASE_URL! },
      stdio: 'pipe',
    })
    const counts = await client.query(`
      SELECT
        (SELECT count(*) FROM reference_planets)
        + (SELECT count(*) FROM reference_signs)
        + (SELECT count(*) FROM reference_aspects)
        + (SELECT count(*) FROM reference_vargas)
        + (SELECT count(*) FROM reference_houses)
        + (SELECT count(*) FROM reference_strength_systems)
        + (SELECT count(*) FROM reference_karakas)
        + (SELECT count(*) FROM reference_upagrahas)
        + (SELECT count(*) FROM reference_constants)
        + (SELECT count(*) FROM reference_topic_tags)
        + (SELECT count(*) FROM reference_glossary) AS total
    `)
    expect(Number(counts.rows[0].total)).toBe(1242)
  }

  async function detector(client: Client): Promise<boolean> {
    const contract = await client.query<{ integrity_check_sql: string }>(
      `SELECT integrity_check_sql FROM asset_registry WHERE asset_id = 'bg_reference'`,
    )
    const result = await client.query(contract.rows[0].integrity_check_sql)
    return result.rowCount === 1 && Object.values(result.rows[0])[0] === true
  }

  it('installs and replays the exact contract, and the healthy detector is true', async () => {
    const client = await connectPrepared()
    try {
      await client.query(migration)
      await client.query(migration)
      await installHealthyFixtures(client)
      expect(await detector(client)).toBe(true)
    } finally {
      await client.end()
    }
  })

  it('fires on representative structural and count-preserving corruptions', async () => {
    const client = await connectPrepared()
    try {
      await client.query(migration)
      await installHealthyFixtures(client)
      const corruptions = [
        "UPDATE reference_planets SET planet_id='pluto' WHERE planet_id='sun'",
        "UPDATE reference_vargas SET varga_id='D99' WHERE varga_id='D60'",
        "UPDATE reference_strength_systems SET strength_id='strength-bogus' WHERE strength_id=(SELECT min(strength_id) FROM reference_strength_systems)",
        "UPDATE reference_karakas SET karaka_id='karaka-bogus' WHERE karaka_id=(SELECT min(karaka_id) FROM reference_karakas)",
        "UPDATE reference_upagrahas SET upagraha_id='upagraha-bogus' WHERE upagraha_id=(SELECT min(upagraha_id) FROM reference_upagrahas)",
        "UPDATE reference_constants SET constant_id='constant-bogus' WHERE constant_id=(SELECT min(constant_id) FROM reference_constants)",
        "UPDATE reference_topic_tags SET name='semantically corrupt' WHERE canonical_id=(SELECT min(canonical_id) FROM reference_topic_tags)",
        "UPDATE reference_glossary SET term_en='semantically corrupt' WHERE term_id=(SELECT min(term_id) FROM reference_glossary)",
        "UPDATE reference_glossary SET classical_citation=' ' WHERE term_id=(SELECT min(term_id) FROM reference_glossary)",
        "DELETE FROM reference_topic_tags WHERE canonical_id=(SELECT min(canonical_id) FROM reference_topic_tags)",
      ]
      await client.query('BEGIN')
      for (const corruption of corruptions) {
        await client.query('SAVEPOINT detector_corruption')
        await client.query(corruption)
        expect(await detector(client)).toBe(false)
        await client.query('ROLLBACK TO SAVEPOINT detector_corruption')
      }
      await client.query('ROLLBACK')
    } finally {
      await client.end()
    }
  })

  it('rejects registry drift without partially installing the contract', async () => {
    const client = await connectPrepared()
    try {
      await client.query("UPDATE asset_registry SET depends_on=ARRAY[]::text[] WHERE asset_id='bg_reference'")
      await expect(client.query(migration)).rejects.toThrow(
        'migration 607 refuses unknown bg_reference registry contract',
      )
      const result = await client.query(
        `SELECT integrity_check_sql FROM asset_registry WHERE asset_id='bg_reference'`,
      )
      expect(result.rows).toEqual([{ integrity_check_sql: null }])
    } finally {
      await client.end()
    }
  })
})
