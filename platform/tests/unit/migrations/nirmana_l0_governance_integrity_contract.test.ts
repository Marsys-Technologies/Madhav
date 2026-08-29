import fs from 'node:fs'
import path from 'node:path'
import { execFileSync } from 'node:child_process'
import { Client } from 'pg'
import { describe, expect, it } from 'vitest'

import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

const migrationPath = path.resolve(
  process.cwd(),
  'supabase/migrations/615_nirmana_l0_governance_integrity_contracts.sql',
)
const integrityMigration = fs.existsSync(migrationPath)
  ? fs.readFileSync(migrationPath, 'utf8')
  : ''
const dependencyMigrationPath = path.resolve(
  process.cwd(),
  'supabase/migrations/635_nirmana_l0_dependency_contracts.sql',
)
const dependencyMigration = fs.existsSync(dependencyMigrationPath)
  ? fs.readFileSync(dependencyMigrationPath, 'utf8')
  : ''
const TEST_DATABASE_URL = process.env.NIRMANA_L0_GOVERNANCE_TEST_DATABASE_URL

if (TEST_DATABASE_URL) {
  const parsed = new URL(TEST_DATABASE_URL)
  if (!['localhost', '127.0.0.1'].includes(parsed.hostname)
    || parsed.pathname !== '/nirmana_l0_governance_integrity_test') {
    throw new Error(
      'NIRMANA_L0_GOVERNANCE_TEST_DATABASE_URL must point to the exact local '
      + 'nirmana_l0_governance_integrity_test database',
    )
  }
}

const HASHES = {
  classPriors: 'a12fd986e469d417ff2ff54d3902b69809d40be42cc2228854220bb63f7139b2',
  lifetimeCounts: '0a7b3be21e8b20a96f5d2a7a820cb1492c9e2e5ed889ff7bfcceec2bb4808800',
  formulaConstants: '14a06b00379e0fc23f00e87984a8e58bc962a1c44849045ff6ac354431576f33',
} as const

describe('migration 615 — scoped L0 governance integrity contracts', () => {
  it('is runner-owned, fail-closed, and aligned with the registry seed', () => {
    expect(integrityMigration).not.toBe('')
    expect(integrityMigration).toContain('migration 615 refuses unknown')
    expect(integrityMigration).not.toMatch(/^BEGIN;/m)
    expect(integrityMigration).not.toMatch(/^COMMIT;/m)
    for (const hash of Object.values(HASHES)) expect(integrityMigration).toContain(hash)
    for (const [assetId, sortOrder, floor] of [
      ['bg_class_priors', 67, 171],
      ['bg_formula_constants', 68, 17],
    ] as const) {
      expect(ASSETS.find(asset => asset.asset_id === assetId)).toMatchObject({
        sort_order: sortOrder,
        target_floor: floor,
        depends_on: [],
      })
    }
    expect(ASSETS.find(asset => asset.asset_id === 'bg_class_lifetime_counts')).toMatchObject({
      sort_order: 21,
      target_floor: 6,
      depends_on: ['bg_ghatana'],
    })
    // 615 must keep validating its original pre-migration state. The new
    // dependency is applied by a later immutable registry-contract migration.
    expect(integrityMigration).toMatch(/asset_id='bg_class_lifetime_counts'[\s\S]*?registry_row\.depends_on=ARRAY\[\]::text\[\]/)
  })
})

describe('migration 635 — source-backed L0 dependency contracts', () => {
  it('is runner-owned, only converges known legacy arrays, and leaves 615 historical validation intact', () => {
    expect(dependencyMigration).not.toBe('')
    expect(dependencyMigration).not.toMatch(/^BEGIN;/m)
    expect(dependencyMigration).not.toMatch(/^COMMIT;/m)
    expect(dependencyMigration).toContain("depends_on = ARRAY[]::text[]")
    expect(dependencyMigration).toContain("depends_on = ARRAY['ga_positions']::text[]")
    expect(dependencyMigration).toContain("depends_on = ARRAY['bg_ghatana']::text[]")
    expect(dependencyMigration).toContain("depends_on = ARRAY['ga_positions', 'bg_panchanga']::text[]")
    expect(dependencyMigration).toContain("depends_on = ARRAY['ga_positions', 'bg_prashna_rules']::text[]")
    expect(dependencyMigration).toContain('migration 635 refuses drifted')
    expect(dependencyMigration).toContain('migration 635 requires CURRENT active source authorities')
    expect(dependencyMigration).toContain('migration 635 requires CURRENT active target contracts')
    expect(dependencyMigration).toContain("health_probe->>'probe_type' = 'panchanga_engine'")
    expect(dependencyMigration).toContain('migration 635 refuses a cycle through a corrected L0 dependency contract')
    expect(integrityMigration).toMatch(/asset_id='bg_class_lifetime_counts'[\s\S]*?registry_row\.depends_on=ARRAY\[\]::text\[\]/)
  })
})

describe.skipIf(!TEST_DATABASE_URL)('L0 governance writers — real PostgreSQL convergence', () => {
  function migration(name: string): string {
    return fs.readFileSync(path.resolve(process.cwd(), 'supabase/migrations', name), 'utf8')
  }

  function runWriters(): void {
    execFileSync('python3', ['-c', [
      'import os, psycopg',
      'from psycopg.rows import dict_row',
      'from brahmagyan.l0_class_priors import seed_class_priors',
      'from brahmagyan.l0_class_lifetime_counts import seed_class_lifetime_counts',
      'from brahmagyan.l0_formula_constants import seed_formula_constants',
      'conn=psycopg.connect(os.environ["NIRMANA_L0_GOVERNANCE_TEST_DATABASE_URL"],row_factory=dict_row)',
      'seed_class_priors(conn,autocommit=False)',
      'seed_class_lifetime_counts(conn,autocommit=False)',
      'seed_formula_constants(conn,autocommit=False)',
      'conn.commit(); conn.close()',
    ].join('; ')], {
      cwd: path.resolve(process.cwd(), 'python-sidecar'),
      env: { ...process.env, NIRMANA_L0_GOVERNANCE_TEST_DATABASE_URL: TEST_DATABASE_URL! },
      stdio: 'pipe',
    })
  }

  async function reset(client: Client): Promise<void> {
    await client.query(`
      DROP TABLE IF EXISTS brahma_class_priors,brahma_formula_constants,asset_registry CASCADE;
      CREATE EXTENSION IF NOT EXISTS pgcrypto;
      CREATE TABLE asset_registry (
        asset_id text PRIMARY KEY,layer text,sort_order integer,sanskrit_name text,
        english_name text,english_description text,storage_type text,target_table text,
        count_sql text,size_sql text,target_floor bigint,depends_on text[] DEFAULT ARRAY[]::text[],
        scope text,is_active boolean,has_writer boolean DEFAULT false,has_substeps boolean DEFAULT false,
        layer_name text,layer_index text,catalog_status text,asset_kind text DEFAULT 'data',
        integrity_check_sql text,volume_explanation text,natural_key_partition text,
        data_disposition text,asset_type text DEFAULT 'data',health_probe jsonb
      );
      CREATE TABLE brahma_class_priors (
        prior_version text NOT NULL,signal_type_class text NOT NULL,fact_kind text NOT NULL,
        source_subsystem text NOT NULL,signal_tradition text NOT NULL,class_prior numeric NOT NULL,
        varga_weights jsonb,contested boolean NOT NULL DEFAULT false,citation text,
        ratified_by text,prior_basis text,source_ref text,created_at timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY(prior_version,signal_type_class,fact_kind,source_subsystem,signal_tradition)
      );
    `)

    // Migration 389 creates the formula table and its original seed. Later
    // migration-owned additions are replayed from their immutable SQL without
    // pulling unrelated schemas into this focused fixture.
    await client.query(migration('389_brahma_formula_constants.sql'))
    const m400 = migration('400_mimamsa_p6_schema.sql')
    await client.query(m400.slice(m400.indexOf('INSERT INTO brahma_formula_constants'), m400.indexOf('COMMIT;')))
    await client.query(migration('408_mi_pramana_drop_manifestation_dimension.sql'))
    await client.query(migration('422_jl009_ph_nimitta_base_rate_age_normalization.sql'))
    const m424 = migration('424_ba_lel_r2_2_calibration_state_persistence.sql')
    await client.query(m424.slice(m424.indexOf('INSERT INTO brahma_formula_constants'), m424.indexOf('COMMIT;')))
    await client.query(`DELETE FROM brahma_formula_constants WHERE constant_id='_bug_ka_sangam_confidence_conflation'`)
    await client.query(`
      INSERT INTO asset_registry
        (asset_id,layer,sort_order,english_description,storage_type,target_table,
         count_sql,target_floor,depends_on,scope,is_active,has_writer,catalog_status,
         asset_kind,volume_explanation)
      VALUES
        ('bg_class_priors','brahmagyan',16,'class priors','postgres_table',
         'brahma_class_priors',
         'SELECT COUNT(*) FROM brahma_class_priors WHERE prior_version=''1.0''',
         171,ARRAY[]::text[],'global',true,true,'CURRENT','data','171 rows'),
        ('bg_class_lifetime_counts','brahmagyan',21,'lifetime counts','postgres_table',
         'brahma_class_priors',
         'SELECT COUNT(*) FROM brahma_class_priors WHERE prior_version=''ne_v01'' AND fact_kind=''lifetime_count_per_100y''',
         6,ARRAY[]::text[],'global',true,true,'CURRENT','data','6 rows');
      UPDATE asset_registry
      SET sort_order=18,target_floor=17,
          count_sql='SELECT count(*) FROM brahma_formula_constants',
          depends_on=ARRAY[]::text[],scope='global',is_active=true,has_writer=true,
          catalog_status='CURRENT',asset_kind='data',volume_explanation='17 rows'
      WHERE asset_id='bg_formula_constants';
    `)
    runWriters()
  }

  async function seedDependencyContracts(client: Client): Promise<void> {
    await client.query(`
      INSERT INTO asset_registry
        (asset_id,layer,depends_on,scope,is_active,has_writer,catalog_status,asset_kind,asset_type,health_probe)
      VALUES
        ('bg_ghatana','brahmagyan',ARRAY[]::text[],'global',true,true,'CURRENT','data','data',NULL),
        ('bg_panchanga','brahmagyan',ARRAY[]::text[],'global',true,false,'CURRENT','service','service','{"probe_type":"panchanga_engine"}'::jsonb),
        ('bg_prashna_rules','brahmagyan',ARRAY[]::text[],'global',true,true,'CURRENT','data','data',NULL),
        ('ga_positions','ganita',ARRAY[]::text[],'per_chart',true,true,'CURRENT','data','data',NULL),
        ('ga_panchanga','ganita',ARRAY['ga_positions']::text[],'per_chart',true,true,'CURRENT','data','data',NULL),
        ('ga_prashna','ganita',ARRAY['ga_positions']::text[],'per_chart',true,true,'CURRENT','data','data',NULL);
    `)
  }

  async function applyMigration(client: Client, sql: string): Promise<void> {
    await client.query('BEGIN')
    try {
      await client.query(sql)
      await client.query('COMMIT')
    } catch (error) {
      await client.query('ROLLBACK')
      throw error
    }
  }

  async function dependencyArrays(client: Client): Promise<Record<string, string[]>> {
    const result = await client.query<{ asset_id: string; depends_on: string[] }>(`
      SELECT asset_id,depends_on
        FROM asset_registry
       WHERE asset_id IN ('bg_class_lifetime_counts','ga_panchanga','ga_prashna')
       ORDER BY asset_id
    `)
    return Object.fromEntries(result.rows.map(row => [row.asset_id, row.depends_on]))
  }

  async function hashes(client: Client): Promise<Record<keyof typeof HASHES, string>> {
    const result = await client.query(`
      SELECT encode(sha256(convert_to(COALESCE(string_agg(
        jsonb_build_array(prior_version,signal_type_class,fact_kind,source_subsystem,
          signal_tradition,class_prior,varga_weights,contested,citation,ratified_by,
          prior_basis,source_ref)::text,E'\\n'
        ORDER BY prior_version COLLATE "C",signal_type_class COLLATE "C",
          fact_kind COLLATE "C",source_subsystem COLLATE "C",signal_tradition COLLATE "C"
      ),''),'UTF8')),'hex') AS digest
      FROM brahma_class_priors WHERE prior_version='1.0';
      SELECT encode(sha256(convert_to(COALESCE(string_agg(
        jsonb_build_array(prior_version,signal_type_class,fact_kind,source_subsystem,
          signal_tradition,class_prior,varga_weights,contested,citation,ratified_by,
          prior_basis,source_ref)::text,E'\\n'
        ORDER BY prior_version COLLATE "C",signal_type_class COLLATE "C",
          fact_kind COLLATE "C",source_subsystem COLLATE "C",signal_tradition COLLATE "C"
      ),''),'UTF8')),'hex') AS digest
      FROM brahma_class_priors
      WHERE prior_version='ne_v01' AND fact_kind='lifetime_count_per_100y';
      SELECT encode(sha256(convert_to(COALESCE(string_agg(
        jsonb_build_array(constant_id,value_jsonb,class,consumer_assets,
          citation_or_ratification,calibratable,bounds,version)::text,E'\\n'
        ORDER BY constant_id COLLATE "C"
      ),''),'UTF8')),'hex') AS digest
      FROM brahma_formula_constants;
    `)
    const rows = result as unknown as Array<{ rows: Array<{ digest: string }> }>
    return {
      classPriors: rows[0].rows[0].digest,
      lifetimeCounts: rows[1].rows[0].digest,
      formulaConstants: rows[2].rows[0].digest,
    }
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

  it('reproduces the three reviewed production partitions', async () => {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    try {
      await reset(client)
      expect(await hashes(client)).toEqual(HASHES)
    } finally {
      await client.end()
    }
  })

  it('applies migration 635 from exact legacy arrays and replays its exact corrected state', async () => {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    try {
      await reset(client)
      await seedDependencyContracts(client)
      await applyMigration(client, dependencyMigration)
      expect(await dependencyArrays(client)).toEqual({
        bg_class_lifetime_counts: ['bg_ghatana'],
        ga_panchanga: ['ga_positions', 'bg_panchanga'],
        ga_prashna: ['ga_positions', 'bg_prashna_rules'],
      })

      await applyMigration(client, dependencyMigration)
      expect(await dependencyArrays(client)).toEqual({
        bg_class_lifetime_counts: ['bg_ghatana'],
        ga_panchanga: ['ga_positions', 'bg_panchanga'],
        ga_prashna: ['ga_positions', 'bg_prashna_rules'],
      })
    } finally {
      await client.end()
    }
  })

  it('fails closed and rolls back migration 635 on an unknown dependency state', async () => {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    try {
      await reset(client)
      await seedDependencyContracts(client)
      await client.query(`UPDATE asset_registry SET depends_on=ARRAY['unreviewed']::text[] WHERE asset_id='ga_panchanga'`)

      await expect(applyMigration(client, dependencyMigration)).rejects.toThrow(
        'migration 635 refuses drifted ga_panchanga dependencies',
      )
      expect(await dependencyArrays(client)).toEqual({
        bg_class_lifetime_counts: [],
        ga_panchanga: ['unreviewed'],
        ga_prashna: ['ga_positions'],
      })
    } finally {
      await client.end()
    }
  })

  it.each([
    ['missing source', `DELETE FROM asset_registry WHERE asset_id='bg_prashna_rules'`, 'migration 635 requires CURRENT active source authorities'],
    ['wrong Panchanga probe type', `UPDATE asset_registry SET health_probe='{"probe_type":"wrong"}'::jsonb WHERE asset_id='bg_panchanga'`, 'migration 635 requires the vetted bg_panchanga service-probe contract'],
    ['cycle through corrected target', `UPDATE asset_registry SET depends_on=ARRAY['bg_class_lifetime_counts']::text[] WHERE asset_id='bg_ghatana'`, 'migration 635 refuses a cycle through a corrected L0 dependency contract'],
  ])('fails closed and rolls back migration 635 on %s', async (_name, setupSql, expectedError) => {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    try {
      await reset(client)
      await seedDependencyContracts(client)
      await client.query(setupSql)

      await expect(applyMigration(client, dependencyMigration)).rejects.toThrow(expectedError)
      expect(await dependencyArrays(client)).toEqual({
        bg_class_lifetime_counts: [],
        ga_panchanga: ['ga_positions'],
        ga_prashna: ['ga_positions'],
      })
    } finally {
      await client.end()
    }
  })

  it('installs, replays, and accepts all three exact partitions', async () => {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    try {
      await reset(client)
      await client.query(integrityMigration)
      await client.query(integrityMigration)
      expect(await detectors(client)).toEqual({
        bg_class_lifetime_counts: true,
        bg_class_priors: true,
        bg_formula_constants: true,
      })
      const metadata = await client.query(
        `SELECT asset_id,sort_order,natural_key_partition,data_disposition
         FROM asset_registry ORDER BY asset_id`,
      )
      expect(metadata.rows).toEqual([
        {
          asset_id: 'bg_class_lifetime_counts', sort_order: 21,
          natural_key_partition: 'prior_version=ne_v01 AND fact_kind=lifetime_count_per_100y; signal_type_class',
          data_disposition: null,
        },
        {
          asset_id: 'bg_class_priors', sort_order: 67,
          natural_key_partition: 'prior_version=1.0; (signal_type_class,fact_kind,source_subsystem,signal_tradition)',
          data_disposition: null,
        },
        {
          asset_id: 'bg_formula_constants', sort_order: 68,
          natural_key_partition: 'constant_id', data_disposition: 'RETAINED_AS_CAPITAL',
        },
      ])
    } finally {
      await client.end()
    }
  })

  it('fires independently on semantic drift in every ownership partition', async () => {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    try {
      await reset(client)
      await client.query(integrityMigration)
      const corruptions = [
        ["UPDATE brahma_class_priors SET citation='drift' WHERE prior_version='1.0' AND signal_type_class='configuration'", 'bg_class_priors'],
        ["UPDATE brahma_class_priors SET citation='drift' WHERE prior_version='ne_v01' AND signal_type_class='marriage'", 'bg_class_lifetime_counts'],
        ["UPDATE brahma_formula_constants SET citation_or_ratification='drift' WHERE constant_id='mi_pramana_scoring_weights'", 'bg_formula_constants'],
      ] as const
      await client.query('BEGIN')
      for (const [sql, assetId] of corruptions) {
        await client.query('SAVEPOINT corruption')
        await client.query(sql)
        const observed = await detectors(client)
        expect(observed[assetId]).toBe(false)
        for (const [otherId, ok] of Object.entries(observed)) {
          if (otherId !== assetId) expect(ok).toBe(true)
        }
        await client.query('ROLLBACK TO SAVEPOINT corruption')
      }
      await client.query('ROLLBACK')
    } finally {
      await client.end()
    }
  })

  it('repairs digest-covered drift without deleting migration-owned constants', async () => {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    try {
      await reset(client)
      await client.query(`
        UPDATE brahma_class_priors
        SET varga_weights='{"drift":1}',contested=true,
            prior_basis='drift',source_ref='drift'
        WHERE prior_version='1.0' AND signal_type_class='configuration';
        UPDATE brahma_class_priors
        SET varga_weights='{"drift":1}',contested=true
        WHERE prior_version='ne_v01' AND signal_type_class='marriage';
        UPDATE brahma_formula_constants SET version='drift'
        WHERE constant_id='combustion_orbs';
      `)
      const migrationOwnedBefore = await client.query(
        `SELECT jsonb_agg(to_jsonb(row_data) ORDER BY constant_id) AS rows
         FROM (SELECT * FROM brahma_formula_constants
               WHERE constant_id NOT IN (
                 'attention_budget','combustion_orbs','dasha_score_flag_threshold',
                 'dignity_scores','holdout_partition','house_weights','magnitude_tiers',
                 'mi_gunanaka_divergence_cap','mi_sambandha_channel_priors',
                 'obstruction_severity_thresholds'
               )) row_data`,
      )
      runWriters()
      expect(await hashes(client)).toEqual(HASHES)
      const migrationOwnedAfter = await client.query(
        `SELECT jsonb_agg(to_jsonb(row_data) ORDER BY constant_id) AS rows
         FROM (SELECT * FROM brahma_formula_constants
               WHERE constant_id NOT IN (
                 'attention_budget','combustion_orbs','dasha_score_flag_threshold',
                 'dignity_scores','holdout_partition','house_weights','magnitude_tiers',
                 'mi_gunanaka_divergence_cap','mi_sambandha_channel_priors',
                 'obstruction_severity_thresholds'
               )) row_data`,
      )
      expect(migrationOwnedAfter.rows[0]).toEqual(migrationOwnedBefore.rows[0])
    } finally {
      await client.end()
    }
  })

  it('rejects registry drift atomically', async () => {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    try {
      await reset(client)
      await client.query(`UPDATE asset_registry SET target_floor=1 WHERE asset_id='bg_class_priors'`)
      await expect(client.query(integrityMigration)).rejects.toThrow(
        'migration 615 refuses unknown bg_class_priors registry contract',
      )
      const observed = await client.query(
        `SELECT count(*) FILTER (WHERE integrity_check_sql IS NOT NULL)::int AS installed,
                max(sort_order) FILTER (WHERE asset_id='bg_formula_constants') AS formula_order
         FROM asset_registry`,
      )
      expect(observed.rows[0]).toEqual({ installed: 0, formula_order: 18 })
    } finally {
      await client.end()
    }
  })
})
