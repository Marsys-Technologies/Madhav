import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import { Client } from 'pg'

import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'supabase/migrations/602_nirmana_l0_achieved_floor_contract.sql'),
  'utf8',
)
const concordanceMigration = fs.readFileSync(
  path.resolve(process.cwd(), 'supabase/migrations/619_nirmana_l0_concordance_integrity_contract.sql'),
  'utf8',
)

describe('migration 602 — Nirmāṇa L0 achieved-floor contract', () => {
  it('fails closed on missing and unknown contracts', () => {
    expect(migration).toContain('migration 602 requires bg_text_index registry row')
    expect(migration).toContain('migration 602 requires bg_concordance registry row')
    expect(migration).toContain('migration 602 requires bg_reference registry row')
    expect(migration).toContain('migration 602 refuses unknown bg_text_index contract')
    expect(migration).toContain('migration 602 refuses unknown bg_concordance contract')
    expect(migration).toContain('migration 602 refuses unknown bg_reference measurement contract')
  })

  it.each([
    ['bg_text_index', 361],
  ])('keeps migration and replay seed aligned for %s', (assetId, achievedFloor) => {
    const asset = ASSETS.find((candidate) => candidate.asset_id === assetId)
    expect(asset?.target_floor).toBe(achievedFloor)
    expect(migration).toMatch(
      new RegExp(`SET target_floor = ${achievedFloor}[\\s\\S]*WHERE asset_id = '${assetId}'`),
    )
  })

  it('keeps migration 602 immutable while migration 619 supersedes the concordance floor', () => {
    const concordance = ASSETS.find((candidate) => candidate.asset_id === 'bg_concordance')
    expect(migration).toMatch(
      /SET target_floor = 720[\s\S]*WHERE asset_id = 'bg_concordance'/,
    )
    expect(concordanceMigration).toContain('SET target_floor = 721')
    expect(concordance?.target_floor).toBe(721)
  })

  it('records the ratified floor provenance and anti-fabrication boundary', () => {
    expect(migration).toContain('ratified by migrations 196 and 231')
    expect(migration).toContain('never fabricate assignments')
  })

  it('aligns bg_reference with its 11-table ownership boundary', () => {
    const reference = ASSETS.find((candidate) => candidate.asset_id === 'bg_reference')
    expect(reference?.target_table).toBe('reference_planets')
    expect(reference?.target_floor).toBe(1242)
    expect(migration).toContain("target_table = 'reference_planets'")
    expect(migration).toContain("count_sql NOT LIKE '%reference_dasha_systems%'")
    expect(migration).toContain("count_sql NOT LIKE '%reference_nakshatras%'")
  })
})

const TEST_DATABASE_URL = process.env.NIRMANA_L0_FLOOR_TEST_DATABASE_URL

describe.skipIf(!TEST_DATABASE_URL)('migration 602 — real Postgres drift behavior', () => {
  it('migrates known legacy state, rejects drift, and preserves it after rollback', async () => {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    try {
      await client.query('BEGIN')
      await client.query(`
        CREATE TEMP TABLE asset_registry (
          asset_id TEXT PRIMARY KEY,
          target_floor INTEGER,
          volume_explanation TEXT,
          target_table TEXT,
          size_sql TEXT,
          count_sql TEXT,
          english_description TEXT
        ) ON COMMIT DROP
      `)
      await client.query(
        `INSERT INTO asset_registry
          (asset_id, target_floor, volume_explanation, target_table, size_sql, count_sql, english_description)
         VALUES
          ('bg_text_index', 400, $1, NULL, NULL, NULL, NULL),
          ('bg_concordance', 800, $2, NULL, NULL, NULL, NULL),
          ('bg_reference', 1485, $5, 'reference_nakshatras',
           'SELECT pg_total_relation_size(''reference_nakshatras'')', $3, $4)`,
        [
          'Distinct topic_tag count from embedded chunks. Floor 400 = topic-vocabulary coverage target; not scaled with chunk count (vocabulary size is independent of corpus depth). Per design §2.2.',
          '800 = topic×school concordance rows. Cross-product metric: cardinality is topic_count × school_count, not chunk-proportional. Chunk-pointer index per (topic, school); synthesis at L1+ query-time.',
          'SELECT (SELECT count(*) FROM reference_planets) + (SELECT count(*) FROM reference_signs) + (SELECT count(*) FROM reference_aspects) + (SELECT count(*) FROM reference_vargas) + (SELECT count(*) FROM reference_houses) + (SELECT count(*) FROM reference_strength_systems) + (SELECT count(*) FROM reference_karakas) + (SELECT count(*) FROM reference_upagrahas) + (SELECT count(*) FROM reference_constants) + (SELECT count(*) FROM reference_topic_tags) + (SELECT count(*) FROM reference_glossary) AS count',
          'The holy grail of L0 — structured properties of every classical Jyotish concept across 15 specialized typed tables.',
          'Sum of 15 reference_* tables (per design §3.2). Each table is normalized + typed; ontology resolves names, reference holds properties.',
        ],
      )

      await client.query(migration)
      const migrated = await client.query(
        `SELECT asset_id, target_floor, target_table, count_sql
         FROM asset_registry ORDER BY asset_id`,
      )
      expect(migrated.rows).toEqual([
        expect.objectContaining({ asset_id: 'bg_concordance', target_floor: 720 }),
        expect.objectContaining({
          asset_id: 'bg_reference',
          target_floor: 1242,
          target_table: 'reference_planets',
          count_sql: expect.not.stringContaining('reference_dasha_systems'),
        }),
        expect.objectContaining({ asset_id: 'bg_text_index', target_floor: 361 }),
      ])

      // Canonical replay must be a successful no-op, not merely first-run safe.
      await expect(client.query(migration)).resolves.toBeDefined()

      // Migrations-only replay reaches the ratified 361/720 floors with the
      // historical 196/197 explanations. Migration 602 must accept exactly
      // those states and canonicalize them to the seed contract.
      await client.query('TRUNCATE asset_registry')
      await client.query(
        `INSERT INTO asset_registry
          (asset_id, target_floor, volume_explanation, target_table, size_sql, count_sql, english_description)
         VALUES
          ('bg_text_index', 361, $1, NULL, NULL, NULL, NULL),
          ('bg_concordance', 720, $2, NULL, NULL, NULL, NULL),
          ('bg_reference', 1485, $3, 'reference_planets',
           'SELECT pg_total_relation_size(''reference_nakshatras'')', $4, $5)`,
        [
          'Distinct topic_tag values present on embedded classical_text_chunks. Grew from 327 to 361 after classifying 1,493 new chunks from bhrigu_nandi_nadi (608) and nadi_navamsa_patel (1,850); 3,716 nadi chunks had no keyword match and remain NULL topic_tag.',
          'Rows in classical_attributions: one per (topic_id × school) pair where the corpus has ≥1 classified chunk. Grew from 477 to 720 after the nadi school dimension was added for bhrigu_nandi_nadi and nadi_navamsa_patel, contributing 243 new (topic × nadi) rows across 361 distinct topics.',
          'bg_reference: 1,269 rows across 12 own reference tables seeded in Tier 0 campaign build 2026-06-09. Tables: reference_planets(11), reference_nakshatras(27), reference_signs(12), reference_aspects(19), reference_vargas(19), reference_houses(12), reference_strength_systems(33), reference_karakas(77), reference_upagrahas(11), reference_constants(203), reference_topic_tags(481), reference_glossary(364). Brief aspiration was ≥1,225 own-12-tables. Floor set to achieved count (1,269).',
          'SELECT (SELECT count(*) FROM reference_planets) + (SELECT count(*) FROM reference_signs) + (SELECT count(*) FROM reference_aspects) + (SELECT count(*) FROM reference_vargas) + (SELECT count(*) FROM reference_houses) + (SELECT count(*) FROM reference_strength_systems) + (SELECT count(*) FROM reference_karakas) + (SELECT count(*) FROM reference_upagrahas) + (SELECT count(*) FROM reference_constants) + (SELECT count(*) FROM reference_topic_tags) + (SELECT count(*) FROM reference_glossary) AS count',
          'The holy grail of L0 — structured properties of every classical Jyotish concept across 15 specialized typed tables.',
        ],
      )
      await client.query(migration)
      const freshReplay = await client.query(
        `SELECT asset_id, target_floor, volume_explanation, english_description
         FROM asset_registry ORDER BY asset_id`,
      )
      expect(freshReplay.rows).toEqual([
        expect.objectContaining({
          asset_id: 'bg_concordance',
          target_floor: 720,
          volume_explanation: expect.stringContaining('ratified by migration 231'),
        }),
        expect.objectContaining({
          asset_id: 'bg_reference',
          target_floor: 1242,
          english_description: expect.stringContaining('11 current typed tables'),
        }),
        expect.objectContaining({
          asset_id: 'bg_text_index',
          target_floor: 361,
          volume_explanation: expect.stringContaining('ratified by migrations 196 and 231'),
        }),
      ])

      await client.query("UPDATE asset_registry SET target_floor = 999 WHERE asset_id = 'bg_text_index'")
      await client.query('SAVEPOINT before_drift_check')
      await expect(client.query(migration)).rejects.toThrow(
        'migration 602 refuses unknown bg_text_index contract',
      )
      await client.query('ROLLBACK TO SAVEPOINT before_drift_check')
      const drift = await client.query(
        "SELECT target_floor FROM asset_registry WHERE asset_id = 'bg_text_index'",
      )
      expect(drift.rows[0].target_floor).toBe(999)
    } finally {
      await client.query('ROLLBACK').catch(() => undefined)
      await client.end()
    }
  })
})
