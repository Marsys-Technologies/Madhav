import fs from 'node:fs'
import path from 'node:path'
import { execFileSync } from 'node:child_process'
import { Client } from 'pg'
import { describe, expect, it } from 'vitest'

import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

const migrationPath = path.resolve(
  process.cwd(),
  'supabase/migrations/614_nirmana_l0_ghatana_integrity_contract.sql',
)
const migration = fs.existsSync(migrationPath) ? fs.readFileSync(migrationPath, 'utf8') : ''
const TEST_DATABASE_URL = process.env.NIRMANA_L0_GHATANA_TEST_DATABASE_URL

if (TEST_DATABASE_URL) {
  const parsed = new URL(TEST_DATABASE_URL)
  if (!['localhost', '127.0.0.1'].includes(parsed.hostname)
    || parsed.pathname !== '/nirmana_l0_ghatana_integrity_test') {
    throw new Error(
      'NIRMANA_L0_GHATANA_TEST_DATABASE_URL must point to the exact local '
      + 'nirmana_l0_ghatana_integrity_test database',
    )
  }
}

const EVENT_HASH = 'ec13daa39559ddbed5556bde597f16514cc815287c094d92b011957d246398c3'
const ACTIVITY_HASH = '261576cc17c10d69d856d74b82f2987094a981a0d58c564294a5bbebd4d70210'
const CANONICAL_DESCRIPTION = 'Global life-event + electional-activity ontology — 27 life-event classes (brahma_event_ontology) and 12 electional activity classes (brahma_activity_ontology), including DR-13 temporal-shape and evidence fields.'
const CANONICAL_EXPLANATION = '27 life-event classes + 12 electional activity classes = 39 total rows, including the five DR-13 coverage extensions.'
const LEGACY_DESCRIPTION = 'Life-event ontology (27 event classes keyed to LEL categories, DR-13 shape-extended 2026-07-19: point/interval/chain temporal shapes, gain-vs-loss evidence_requirements, self_report_non_discriminating flags, kill_switch_criteria) + electional activity ontology (12 muhurta activity classes). Seeded from W1 seed package Sections 5-6; shape/evidence/self-report/kill-switch fields added by D-4a Lane A-2. Governs L4 ph_nimitta, L4 ph_muhurta, the D-4a matcher (A-1), and the D-4a prospective ledger (A-4) claim_shape validation.'

describe('migration 614 — Ghatana integrity contract', () => {
  it('is runner-owned, fail-closed, and aligned with the registry seed', () => {
    expect(migration).not.toBe('')
    expect(migration).toContain('migration 614 refuses unknown registry contract')
    expect(migration).not.toMatch(/^BEGIN;/m)
    expect(migration).not.toMatch(/^COMMIT;/m)
    expect(migration).toContain(EVENT_HASH)
    expect(migration).toContain(ACTIVITY_HASH)
    expect(ASSETS.find(asset => asset.asset_id === 'bg_ghatana')).toMatchObject({
      sort_order: 16,
      target_table: 'brahma_event_ontology',
      count_sql: 'SELECT (SELECT count(*) FROM brahma_event_ontology) + (SELECT count(*) FROM brahma_activity_ontology) AS count',
      target_floor: 39,
      depends_on: [],
    })
  })
})

describe.skipIf(!TEST_DATABASE_URL)('bg_ghatana writer convergence — real PostgreSQL behavior', () => {
  function runWriter(): void {
    execFileSync('python3', ['-c', [
      'import os, psycopg',
      'from psycopg.rows import dict_row',
      'from brahmagyan.l0_ghatana import seed_ghatana',
      'conn=psycopg.connect(os.environ["NIRMANA_L0_GHATANA_TEST_DATABASE_URL"],row_factory=dict_row)',
      'seed_ghatana(conn)',
      'conn.close()',
    ].join('; ')], {
      cwd: path.resolve(process.cwd(), 'python-sidecar'),
      env: { ...process.env, NIRMANA_L0_GHATANA_TEST_DATABASE_URL: TEST_DATABASE_URL! },
      stdio: 'pipe',
    })
  }

  async function resetToCanonicalMigrations(client: Client): Promise<void> {
    await client.query(`
      DROP TABLE IF EXISTS brahma_activity_ontology,brahma_event_ontology,asset_registry CASCADE;
      CREATE EXTENSION IF NOT EXISTS pgcrypto;
      CREATE TABLE asset_registry (
        asset_id text PRIMARY KEY, layer text, sort_order integer,
        sanskrit_name text, english_name text, english_description text,
        storage_type text, target_table text, count_sql text, size_sql text,
        target_floor bigint, scope text, is_active boolean, layer_name text,
        layer_index text, catalog_status text, has_writer boolean DEFAULT false,
        asset_kind text DEFAULT 'data', depends_on text[] DEFAULT ARRAY[]::text[],
        integrity_check_sql text, volume_explanation text,
        data_disposition text, natural_key_partition text
      );
    `)
    for (const file of [
      '388_brahma_ghatana_ontology.sql',
      '421_jl009_bereavement_baserate_ontology_v1_1.sql',
      '456_brahma_event_ontology_dr13_shapes.sql',
      '555_brahma_event_ontology_g9_reconcile.sql',
    ]) {
      await client.query(fs.readFileSync(
        path.resolve(process.cwd(), 'supabase/migrations', file),
        'utf8',
      ))
    }
    await client.query(`
      UPDATE asset_registry
      SET sort_order=16,
          asset_kind='data',
          depends_on=ARRAY[]::text[],
          target_floor=39,
          count_sql='SELECT (SELECT count(*) FROM brahma_event_ontology) + (SELECT count(*) FROM brahma_activity_ontology) AS count',
          english_description=$$${CANONICAL_DESCRIPTION}$$,
          volume_explanation=$$${CANONICAL_EXPLANATION}$$
      WHERE asset_id='bg_ghatana'
    `)
  }

  async function eventHash(client: Client): Promise<string> {
    const observed = await client.query<{ digest: string }>(`
      SELECT encode(sha256(convert_to(COALESCE(string_agg(
        jsonb_build_array(event_class_id,name_en,domain,lel_category,
          signature_model,magnitude_floor,adjacency,base_rate_by_age,
          matching_rules,citations,version,temporal_shape,duration_prior,
          milestone_template,irreversibility_milestone,evidence_requirements,
          self_report_non_discriminating,kill_switch_criteria)::text,
        E'\\n' ORDER BY event_class_id COLLATE "C"
      ),''),'UTF8')),'hex') AS digest
      FROM brahma_event_ontology
    `)
    return observed.rows[0].digest
  }

  async function detector(client: Client): Promise<boolean> {
    const contract = await client.query<{ integrity_check_sql: string }>(
      `SELECT integrity_check_sql FROM asset_registry WHERE asset_id='bg_ghatana'`,
    )
    const observed = await client.query(contract.rows[0].integrity_check_sql)
    return observed.rowCount === 1 && Object.values(observed.rows[0])[0] === true
  }

  it('preserves migration-owned fields and reproduces the reviewed production event ontology', async () => {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    try {
      await resetToCanonicalMigrations(client)
      expect(await eventHash(client)).not.toBe(EVENT_HASH)
      runWriter()
      expect(await eventHash(client)).toBe(EVENT_HASH)
    } finally {
      await client.end()
    }
  })

  it('installs, replays, and accepts the exact composite ontology', async () => {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    try {
      await resetToCanonicalMigrations(client)
      runWriter()
      // Migration 604 canonicalizes the floor/prose but intentionally leaves
      // production's historical sort_order=17. This is the actual deploy-time
      // state immediately before migration 614.
      await client.query(`UPDATE asset_registry SET sort_order=17 WHERE asset_id='bg_ghatana'`)
      await client.query(migration)
      await client.query(migration)
      expect(await detector(client)).toBe(true)
      const registry = await client.query(
        `SELECT sort_order,target_floor,english_description,volume_explanation,
                natural_key_partition,data_disposition
         FROM asset_registry WHERE asset_id='bg_ghatana'`,
      )
      expect(registry.rows[0]).toEqual({
        sort_order: 16,
        target_floor: '39',
        english_description: CANONICAL_DESCRIPTION,
        volume_explanation: CANONICAL_EXPLANATION,
        natural_key_partition: 'brahma_event_ontology.event_class_id; brahma_activity_ontology.activity_class_id',
        data_disposition: 'RETAINED_AS_CAPITAL',
      })
    } finally {
      await client.end()
    }
  })

  it('canonicalizes the exact live pre-604 registry state atomically', async () => {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    try {
      await resetToCanonicalMigrations(client)
      runWriter()
      await client.query(`
        UPDATE asset_registry
        SET sort_order=17,
            target_floor=NULL,
            count_sql='SELECT (SELECT COUNT(*) FROM brahma_event_ontology) + (SELECT COUNT(*) FROM brahma_activity_ontology) AS count',
            english_description=$$${LEGACY_DESCRIPTION}$$,
            volume_explanation=NULL
        WHERE asset_id='bg_ghatana'
      `)
      await client.query(migration)
      const registry = await client.query(
        `SELECT sort_order,target_floor,count_sql,english_description,volume_explanation,
                integrity_check_sql IS NOT NULL AS installed
         FROM asset_registry WHERE asset_id='bg_ghatana'`,
      )
      expect(registry.rows[0]).toEqual({
        sort_order: 16,
        target_floor: '39',
        count_sql: 'SELECT (SELECT count(*) FROM brahma_event_ontology) + (SELECT count(*) FROM brahma_activity_ontology) AS count',
        english_description: CANONICAL_DESCRIPTION,
        volume_explanation: CANONICAL_EXPLANATION,
        installed: true,
      })
    } finally {
      await client.end()
    }
  })

  it('fires on semantic drift in writer-owned and migration-owned fields', async () => {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    try {
      await resetToCanonicalMigrations(client)
      runWriter()
      await client.query(migration)
      const corruptions = [
        `UPDATE brahma_event_ontology SET signature_model='{}' WHERE event_class_id='career_entry'`,
        `UPDATE brahma_event_ontology SET matching_rules='{}' WHERE event_class_id='birth_anchor'`,
        `UPDATE brahma_activity_ontology SET citations=ARRAY['drift'] WHERE activity_class_id='marriage'`,
      ]
      await client.query('BEGIN')
      for (const sql of corruptions) {
        await client.query('SAVEPOINT corruption')
        await client.query(sql)
        expect(await detector(client)).toBe(false)
        await client.query('ROLLBACK TO SAVEPOINT corruption')
      }
      await client.query('ROLLBACK')
    } finally {
      await client.end()
    }
  })

  it('repairs writer-owned drift on replay without replacing retained fields', async () => {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    try {
      await resetToCanonicalMigrations(client)
      runWriter()
      await client.query(migration)
      const retained = await client.query(
        `SELECT matching_rules,evidence_requirements,kill_switch_criteria
         FROM brahma_event_ontology WHERE event_class_id='birth_anchor'`,
      )
      await client.query(`
        UPDATE brahma_event_ontology
        SET name_en='drift',signature_model='{}',temporal_shape='interval',
            duration_prior='{"min_days":1,"typical_days":1,"max_days":1}'
        WHERE event_class_id='birth_anchor';
        UPDATE brahma_activity_ontology
        SET name_en='drift',related_event_class=NULL,version='drift'
        WHERE activity_class_id='marriage';
      `)
      expect(await detector(client)).toBe(false)
      runWriter()
      expect(await detector(client)).toBe(true)
      const after = await client.query(
        `SELECT matching_rules,evidence_requirements,kill_switch_criteria
         FROM brahma_event_ontology WHERE event_class_id='birth_anchor'`,
      )
      expect(after.rows[0]).toEqual(retained.rows[0])
      const ownedEvent = await client.query(
        `SELECT event_class_id,name_en,temporal_shape,duration_prior
         FROM brahma_event_ontology WHERE event_class_id='birth_anchor'`,
      )
      const ownedActivity = await client.query(
        `SELECT activity_class_id,name_en,related_event_class,version
         FROM brahma_activity_ontology WHERE activity_class_id='marriage'`,
      )
      expect(ownedEvent.rows[0]).toEqual({
        event_class_id: 'birth_anchor',
        name_en: "Birth (Subject's Own, Chart Epoch)",
        temporal_shape: 'point',
        duration_prior: null,
      })
      expect(ownedActivity.rows[0]).toEqual({
        activity_class_id: 'marriage',
        name_en: 'Marriage',
        related_event_class: 'marriage',
        version: '1.0',
      })
    } finally {
      await client.end()
    }
  })

  it('rejects registry drift atomically', async () => {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    try {
      await resetToCanonicalMigrations(client)
      runWriter()
      await client.query(`UPDATE asset_registry SET target_floor=1 WHERE asset_id='bg_ghatana'`)
      await expect(client.query(migration)).rejects.toThrow(
        'migration 614 refuses unknown registry contract',
      )
      const observed = await client.query(
        `SELECT integrity_check_sql,natural_key_partition,data_disposition
         FROM asset_registry WHERE asset_id='bg_ghatana'`,
      )
      expect(observed.rows[0]).toEqual({
        integrity_check_sql: null,
        natural_key_partition: null,
        data_disposition: null,
      })
    } finally {
      await client.end()
    }
  })
})
