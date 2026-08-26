import fs from 'node:fs'
import path from 'node:path'
import { execFileSync } from 'node:child_process'
import { Client } from 'pg'
import { describe, expect, it } from 'vitest'

import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

const migrationPath = path.resolve(
  process.cwd(),
  'supabase/migrations/616_nirmana_l0_prashna_integrity_contract.sql',
)
const migration = fs.existsSync(migrationPath) ? fs.readFileSync(migrationPath, 'utf8') : ''
const TEST_DATABASE_URL = process.env.NIRMANA_L0_PRASHNA_TEST_DATABASE_URL

const HASHES = [
  '1fcf4a29aada13aeb3458a601f42206111cdd0e7132f1d3973f49b65de239b11',
  'd67e84e57e5c616f132929e845dec3ee8d5fccd4d9530d9c5c90b0a275662638',
  '8a02f4bd19ad23ab67ec1b7354d6c537e0c54453d4a6c405caf033c630879427',
  '96ac27661e071bac4e372272f4eea1472cca37c0b47dbd7d9f07b37f159a99a0',
  '065791ee29ce9a1c6b98ed9d356151b06e0a463b1bcb02c9904ea160846488cd',
] as const

const canonicalExplanation = '41 rows across 5 prashna sub-tables (5 lagna methods + 16 Tajik yogas + 12 significators + 5 fructification rules + 3 special techniques).'

describe('migration 616 — Prashna producer integrity contract', () => {
  it('is runner-owned, fail-closed, and aligned with the complete source corpus', () => {
    expect(migration).not.toBe('')
    expect(migration).toContain('migration 616 refuses unknown bg_prashna_rules registry contract')
    expect(migration).not.toMatch(/^BEGIN;/m)
    expect(migration).not.toMatch(/^COMMIT;/m)
    for (const hash of HASHES) expect(migration).toContain(hash)
    expect(ASSETS.find(asset => asset.asset_id === 'bg_prashna_rules')).toMatchObject({
      sort_order: 55,
      target_table: null,
      target_floor: 41,
      volume_explanation: canonicalExplanation,
      depends_on: [],
    })
  })
})

if (TEST_DATABASE_URL) {
  const parsed = new URL(TEST_DATABASE_URL)
  if (!['localhost', '127.0.0.1'].includes(parsed.hostname)
    || parsed.pathname !== '/nirmana_l0_prashna_integrity_test') {
    throw new Error(
      'NIRMANA_L0_PRASHNA_TEST_DATABASE_URL must point to the exact local '
      + 'nirmana_l0_prashna_integrity_test database',
    )
  }
}

describe.skipIf(!TEST_DATABASE_URL)('migration 616 — real PostgreSQL behavior', () => {
  function runWriter(): void {
    execFileSync('python3', ['-c', [
      'import os, psycopg',
      'from brahmagyan.l0_prashna import seed_prashna_rules',
      'conn=psycopg.connect(os.environ["NIRMANA_L0_PRASHNA_TEST_DATABASE_URL"])',
      'seed_prashna_rules(conn)',
      'conn.commit(); conn.close()',
    ].join('; ')], {
      cwd: path.resolve(process.cwd(), 'python-sidecar'),
      env: { ...process.env, NIRMANA_L0_PRASHNA_TEST_DATABASE_URL: TEST_DATABASE_URL! },
      stdio: 'pipe',
    })
  }

  async function connectPrepared(): Promise<Client> {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    await client.query(`
      CREATE EXTENSION IF NOT EXISTS pgcrypto;
      DROP TABLE IF EXISTS bg_prashna_special_techniques,
        bg_prashna_fructification_rules,bg_prashna_significators,
        bg_prashna_tajik_yogas,bg_prashna_lagna_methods,asset_registry CASCADE;
      CREATE TABLE asset_registry (
        asset_id text PRIMARY KEY, layer text, sort_order integer, scope text,
        asset_kind text, catalog_status text, is_active boolean, has_writer boolean,
        target_table text, count_sql text, target_floor bigint, depends_on text[],
        natural_key_partition text, data_disposition text, integrity_check_sql text,
        english_description text, volume_explanation text
      );
      CREATE TABLE bg_prashna_lagna_methods (
        id serial PRIMARY KEY, method_id text UNIQUE NOT NULL, method_name text NOT NULL,
        method_name_sa text, derivation_rule text NOT NULL, derivation_rule_jsonb jsonb,
        classical_citation text NOT NULL, is_primary boolean DEFAULT false,
        tradition text NOT NULL
      );
      CREATE TABLE bg_prashna_tajik_yogas (
        id serial PRIMARY KEY, yoga_id text UNIQUE NOT NULL, yoga_name text NOT NULL,
        yoga_name_sa text, judgment_meaning text NOT NULL, formation_rule text NOT NULL,
        formation_rule_jsonb jsonb, classical_citation text NOT NULL,
        is_fructification_indicator boolean DEFAULT false
      );
      CREATE TABLE bg_prashna_significators (
        id serial PRIMARY KEY, question_class text UNIQUE NOT NULL, querent_house integer,
        querent_planet text, quesited_house integer NOT NULL, quesited_planet text,
        significator_rule text NOT NULL, classical_citation text NOT NULL
      );
      CREATE TABLE bg_prashna_fructification_rules (
        id serial PRIMARY KEY, rule_id text UNIQUE NOT NULL, time_unit text NOT NULL,
        degree_conversion_rule text NOT NULL, applicable_when text NOT NULL,
        classical_citation text NOT NULL
      );
      CREATE TABLE bg_prashna_special_techniques (
        id serial PRIMARY KEY, technique_id text UNIQUE NOT NULL,
        technique_name text NOT NULL, technique_name_sa text,
        application_rule text NOT NULL, classical_citation text NOT NULL
      );
      INSERT INTO asset_registry
        (asset_id,layer,sort_order,scope,asset_kind,catalog_status,is_active,
         has_writer,target_table,count_sql,target_floor,depends_on,
         natural_key_partition,data_disposition,integrity_check_sql,
         english_description,volume_explanation)
      VALUES
        ('bg_prashna_rules','brahmagyan',55,'global','data','CURRENT',true,true,
         NULL,
         'SELECT (SELECT COUNT(*) FROM bg_prashna_lagna_methods) + (SELECT COUNT(*) FROM bg_prashna_tajik_yogas) + (SELECT COUNT(*) FROM bg_prashna_significators) + (SELECT COUNT(*) FROM bg_prashna_fructification_rules) + (SELECT COUNT(*) FROM bg_prashna_special_techniques) AS count',
         41,ARRAY[]::text[],NULL,NULL,NULL,
         'Static horary astrology rules — Prashna lagna methods, Tajik yogas, significators, fructification rules, and special techniques.',
         '${canonicalExplanation}');
    `)
    runWriter()
    return client
  }

  async function detector(client: Client): Promise<boolean> {
    const contract = await client.query<{ integrity_check_sql: string }>(
      `SELECT integrity_check_sql FROM asset_registry WHERE asset_id='bg_prashna_rules'`,
    )
    const observed = await client.query(contract.rows[0].integrity_check_sql)
    return observed.rowCount === 1 && Object.values(observed.rows[0])[0] === true
  }

  it('installs, replays, and accepts the exact five-table writer output', async () => {
    const client = await connectPrepared()
    try {
      await client.query(migration)
      await client.query(migration)
      expect(await detector(client)).toBe(true)
      const registry = await client.query(
        `SELECT target_floor,volume_explanation,natural_key_partition,
                data_disposition,integrity_check_sql IS NOT NULL AS has_integrity
         FROM asset_registry WHERE asset_id='bg_prashna_rules'`,
      )
      expect(registry.rows[0]).toEqual({
        target_floor: '41',
        volume_explanation: canonicalExplanation,
        natural_key_partition: 'bg_prashna_lagna_methods.method_id; bg_prashna_tajik_yogas.yoga_id; bg_prashna_significators.question_class; bg_prashna_fructification_rules.rule_id; bg_prashna_special_techniques.technique_id',
        data_disposition: null,
        has_integrity: true,
      })
    } finally {
      await client.end()
    }
  })

  it('fires on every component and the writer repairs source-owned semantic drift', async () => {
    const client = await connectPrepared()
    try {
      await client.query(migration)
      const corruptions = [
        "UPDATE bg_prashna_lagna_methods SET derivation_rule='drift' WHERE method_id='kp_249'",
        "UPDATE bg_prashna_tajik_yogas SET formation_rule='drift' WHERE yoga_id='ikbal'",
        "UPDATE bg_prashna_significators SET significator_rule='drift' WHERE question_class='career'",
        "UPDATE bg_prashna_fructification_rules SET applicable_when='drift' WHERE rule_id='degree_to_days'",
        "UPDATE bg_prashna_special_techniques SET application_rule='drift' WHERE technique_id='nashta_jataka'",
      ]
      for (const sql of corruptions) {
        await client.query(sql)
        expect(await detector(client)).toBe(false)
        runWriter()
        expect(await detector(client)).toBe(true)
      }
    } finally {
      await client.end()
    }
  })

  it('rejects unowned accretion and registry drift', async () => {
    const client = await connectPrepared()
    try {
      await client.query(migration)
      await client.query(`
        INSERT INTO bg_prashna_special_techniques
          (technique_id,technique_name,application_rule,classical_citation)
        VALUES ('rogue','Rogue','not source-owned','none')
      `)
      expect(await detector(client)).toBe(false)
      await client.query(`DELETE FROM bg_prashna_special_techniques WHERE technique_id='rogue'`)
      expect(await detector(client)).toBe(true)

      await client.query(`UPDATE asset_registry SET target_floor=1 WHERE asset_id='bg_prashna_rules'`)
      await expect(client.query(migration)).rejects.toThrow(
        'migration 616 refuses unknown bg_prashna_rules registry contract',
      )
      const observed = await client.query(
        `SELECT target_floor,integrity_check_sql IS NOT NULL AS has_integrity
         FROM asset_registry WHERE asset_id='bg_prashna_rules'`,
      )
      expect(observed.rows[0]).toEqual({ target_floor: '1', has_integrity: true })
    } finally {
      await client.end()
    }
  })
})
