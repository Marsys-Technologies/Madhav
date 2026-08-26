import { createHash } from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { Client } from 'pg'
import { describe, expect, it } from 'vitest'

import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

const migrationPath = path.resolve(
  process.cwd(),
  'supabase/migrations/604_nirmana_l0_registry_scope_contract.sql',
)
const migration = fs.readFileSync(migrationPath, 'utf8')

const OLD_SPEC_SHA = 'ddab67f339af980fd4092270d6ed598189524d73b7d295a79e9f449fc64bd6c1'
type DigestSpec = {
  components: Array<{
    key_columns: string[]
    name: string
    relation: string
    value_columns: string[]
    where_equals?: Record<string, string>
  }>
  version: string
}

const OLD_SPEC: DigestSpec = {
  components: [{
    key_columns: ['prior_version', 'signal_type_class', 'fact_kind', 'source_subsystem', 'signal_tradition'],
    name: 'brahma_class_priors',
    relation: 'brahma_class_priors',
    value_columns: [
      'prior_version', 'signal_type_class', 'fact_kind', 'source_subsystem',
      'signal_tradition', 'class_prior', 'varga_weights', 'contested',
      'citation', 'ratified_by', 'prior_basis', 'source_ref',
    ],
  }],
  version: 'nirmana-output-digest-spec-v1',
}

function canonicalize(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonicalize)
  if (value !== null && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([key, child]) => [key, canonicalize(child)]),
    )
  }
  return value
}

function canonicalDigest(value: unknown): string {
  return createHash('sha256').update(JSON.stringify(canonicalize(value))).digest('hex')
}

function migrationSpecs(): Map<string, { sha: string, spec: DigestSpec }> {
  return new Map(
    [...migration.matchAll(
      /\(\s*'([^']+)',\s*'([a-f0-9]{64})',\s*'({.+?})'::jsonb\s*\)/gs,
    )].map((match) => [
      match[1],
      { sha: match[2], spec: JSON.parse(match[3]) as DigestSpec },
    ]),
  )
}

describe('migration 604 — Nirmāṇa L0 registry ownership scopes', () => {
  it('supersedes rather than deletes the shared-table digest specifications', () => {
    expect(migration).toContain('UPDATE asset_output_digest_specs')
    expect(migration).toContain('SET retired_at = clock_timestamp()')
    expect(migration).not.toMatch(/DELETE FROM asset_output_digest_specs/i)
    expect(migration).toContain(OLD_SPEC_SHA)
    expect(migration).toContain('migration 604 refuses unknown current class-prior digest specification')
  })

  it('partitions the shared table by immutable writer-owned coordinates', () => {
    const specs = migrationSpecs()
    expect([...specs.keys()].sort()).toEqual([
      'bg_class_lifetime_counts',
      'bg_class_priors',
    ])
    expect(specs.get('bg_class_priors')?.spec.components[0].where_equals).toEqual({
      prior_version: '1.0',
    })
    expect(specs.get('bg_class_lifetime_counts')?.spec.components[0].where_equals).toEqual({
      fact_kind: 'lifetime_count_per_100y',
      prior_version: 'ne_v01',
    })
    for (const { sha, spec } of specs.values()) {
      expect(canonicalDigest(spec)).toBe(sha)
    }
  })

  it('keeps registry replay metadata aligned with measured achieved output', () => {
    const expected = [
      ['bg_class_priors', 171, "SELECT COUNT(*) FROM brahma_class_priors WHERE prior_version='1.0'"],
      ['bg_class_lifetime_counts', 6, "SELECT COUNT(*) FROM brahma_class_priors WHERE prior_version='ne_v01' AND fact_kind='lifetime_count_per_100y'"],
      ['bg_ghatana', 39, 'SELECT (SELECT count(*) FROM brahma_event_ontology) + (SELECT count(*) FROM brahma_activity_ontology) AS count'],
    ] as const

    for (const [assetId, floor, countSql] of expected) {
      const asset = ASSETS.find((candidate) => candidate.asset_id === assetId)
      expect(asset?.target_floor).toBe(floor)
      expect(asset?.count_sql).toBe(countSql)
      expect(migration).toContain(`WHERE asset_id = '${assetId}'`)
    }
    expect(ASSETS.find((asset) => asset.asset_id === 'bg_class_priors')?.volume_explanation)
      .toContain('24 classes + 12 subsystems + 6 traditions + 30 vargas + 99 graha x domain')
    expect(ASSETS.find((asset) => asset.asset_id === 'bg_ghatana')?.volume_explanation)
      .toContain('27 life-event classes + 12 electional activity classes = 39 total rows')
  })

  it('leaves transaction ownership with the migration runner', () => {
    expect(migration).not.toMatch(/^BEGIN;/m)
    expect(migration).not.toMatch(/^COMMIT;/m)
  })
})

const TEST_DATABASE_URL = process.env.NIRMANA_L0_REGISTRY_SCOPE_TEST_DATABASE_URL

if (TEST_DATABASE_URL) {
  const parsed = new URL(TEST_DATABASE_URL)
  if (!['localhost', '127.0.0.1'].includes(parsed.hostname)
    || parsed.pathname !== '/nirmana_l0_registry_scope_test') {
    throw new Error(
      'NIRMANA_L0_REGISTRY_SCOPE_TEST_DATABASE_URL must point to the exact local '
      + 'nirmana_l0_registry_scope_test database',
    )
  }
}

describe.skipIf(!TEST_DATABASE_URL)('migration 604 — real Postgres behavior', () => {
  async function connectPrepared(): Promise<Client> {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    await client.query(`
      CREATE TEMP TABLE asset_registry (
        asset_id text PRIMARY KEY,
        target_floor integer,
        count_sql text,
        volume_explanation text,
        english_description text
      );
      CREATE TEMP TABLE asset_output_digest_specs (
        asset_id text NOT NULL REFERENCES asset_registry(asset_id) ON DELETE RESTRICT,
        spec_sha256 text NOT NULL,
        spec jsonb NOT NULL,
        reviewed_at timestamptz NOT NULL DEFAULT now(),
        retired_at timestamptz,
        PRIMARY KEY (asset_id, spec_sha256),
        CHECK (retired_at IS NULL OR retired_at >= reviewed_at)
      );
      CREATE UNIQUE INDEX asset_output_digest_specs_one_current_test
        ON asset_output_digest_specs (asset_id) WHERE retired_at IS NULL;
      CREATE TEMP TABLE asset_provenance_receipts (
        receipt_id text PRIMARY KEY,
        asset_id text NOT NULL,
        output_digest_spec_sha256 text,
        FOREIGN KEY (asset_id, output_digest_spec_sha256)
          REFERENCES asset_output_digest_specs(asset_id, spec_sha256)
          ON DELETE RESTRICT
      );
    `)
    await client.query(
      `INSERT INTO asset_registry
        (asset_id, target_floor, count_sql, volume_explanation, english_description)
       VALUES
        ('bg_class_priors', NULL, 'SELECT COUNT(*) FROM brahma_class_priors', NULL, $1),
        ('bg_class_lifetime_counts', 0,
         'SELECT COUNT(*) FROM brahma_class_priors WHERE fact_kind=''lifetime_count_per_100y''',
         NULL, $2),
        ('bg_ghatana', NULL,
         'SELECT (SELECT COUNT(*) FROM brahma_event_ontology) + (SELECT COUNT(*) FROM brahma_activity_ontology) AS count',
         NULL, $3)`,
      [
        'Ranked salience class-prior weights for composite query-time ranking. 4 axes: signal_type_class × source_subsystem × signal_tradition × varga × graha×domain. Seeded from W1 judgment package v1.0; versioned; L5-calibratable.',
        'ṢAḌ-DARŚANA W2 (ADJUDICATION-2): N_e — the expected lifetime count of each brahma_event_ontology event class over a 100-year modelled timeline from birth, assuming survival. The chart-INDEPENDENT structural baseline λ⁰_e of the Kāla Kṣetra hazard field. Every value is Tier N-i: a published demographic / actuarial / epidemiological statistic carrying publisher, edition, year, indicator id, geography+cohort and a retrievable URL/DOI, together with the arithmetic converting it to a per-100-year count — or Tier N-ii, a stated arithmetic identity over such a value. Classical-text counts are FORECLOSED (chart-conditional; already carried by P_e) and cohort/LEL-derived counts are FORECLOSED by the circularity guard. A class with no defensible source is NOT seeded and is honestly skipped by ka_kshetra with no_class_prior_row — honest-empty per class, never a fabricated baseline.',
        'Life-event ontology (27 event classes keyed to LEL categories, DR-13 shape-extended 2026-07-19: point/interval/chain temporal shapes, gain-vs-loss evidence_requirements, self_report_non_discriminating flags, kill_switch_criteria) + electional activity ontology (12 muhurta activity classes). Seeded from W1 seed package Sections 5-6; shape/evidence/self-report/kill-switch fields added by D-4a Lane A-2. Governs L4 ph_nimitta, L4 ph_muhurta, the D-4a matcher (A-1), and the D-4a prospective ledger (A-4) claim_shape validation.',
      ],
    )
    for (const assetId of ['bg_class_priors', 'bg_class_lifetime_counts']) {
      await client.query(
        `INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
         VALUES ($1, $2, $3::jsonb)`,
        [assetId, OLD_SPEC_SHA, JSON.stringify(OLD_SPEC)],
      )
    }
    await client.query(
      `INSERT INTO asset_provenance_receipts
        (receipt_id, asset_id, output_digest_spec_sha256)
       VALUES ('historical-receipt', 'bg_class_priors', $1)`,
      [OLD_SPEC_SHA],
    )
    return client
  }

  it('retires old specs, preserves receipts, scopes current specs, and replays', async () => {
    const client = await connectPrepared()
    try {
      await client.query(migration)
      await client.query(migration)

      const specs = await client.query(
        `SELECT asset_id, spec_sha256, spec, retired_at IS NULL AS current
         FROM asset_output_digest_specs ORDER BY asset_id, current`,
      )
      expect(specs.rows).toHaveLength(4)
      expect(specs.rows.filter((row) => row.current)).toHaveLength(2)
      expect(specs.rows.filter((row) => !row.current).map((row) => row.spec_sha256))
        .toEqual([OLD_SPEC_SHA, OLD_SPEC_SHA])
      expect(specs.rows.find((row) => row.asset_id === 'bg_class_priors' && row.current)
        ?.spec.components[0].where_equals).toEqual({ prior_version: '1.0' })
      expect(specs.rows.find((row) => row.asset_id === 'bg_class_lifetime_counts' && row.current)
        ?.spec.components[0].where_equals).toEqual({
          fact_kind: 'lifetime_count_per_100y',
          prior_version: 'ne_v01',
        })

      const receipt = await client.query(
        'SELECT output_digest_spec_sha256 FROM asset_provenance_receipts',
      )
      expect(receipt.rows).toEqual([{ output_digest_spec_sha256: OLD_SPEC_SHA }])

      const registry = await client.query(
        `SELECT asset_id, target_floor, count_sql FROM asset_registry ORDER BY asset_id`,
      )
      expect(registry.rows).toEqual([
        {
          asset_id: 'bg_class_lifetime_counts',
          target_floor: 6,
          count_sql: "SELECT COUNT(*) FROM brahma_class_priors WHERE prior_version='ne_v01' AND fact_kind='lifetime_count_per_100y'",
        },
        {
          asset_id: 'bg_class_priors',
          target_floor: 171,
          count_sql: "SELECT COUNT(*) FROM brahma_class_priors WHERE prior_version='1.0'",
        },
        {
          asset_id: 'bg_ghatana',
          target_floor: 39,
          count_sql: 'SELECT (SELECT count(*) FROM brahma_event_ontology) + (SELECT count(*) FROM brahma_activity_ontology) AS count',
        },
      ])
    } finally {
      await client.end()
    }
  })

  it('rejects registry drift without superseding either current spec', async () => {
    const client = await connectPrepared()
    try {
      await client.query(
        `UPDATE asset_registry SET target_floor = 999 WHERE asset_id = 'bg_class_priors'`,
      )
      await expect(client.query(migration)).rejects.toThrow(
        'migration 604 refuses unknown bg_class_priors registry contract',
      )
      const current = await client.query(
        `SELECT count(*)::int AS count FROM asset_output_digest_specs WHERE retired_at IS NULL`,
      )
      expect(current.rows[0].count).toBe(2)
    } finally {
      await client.end()
    }
  })

  it('rejects an unknown current digest contract before retiring it', async () => {
    const client = await connectPrepared()
    try {
      await client.query(
        `UPDATE asset_output_digest_specs
         SET spec = spec || '{"unexpected":true}'::jsonb
         WHERE asset_id = 'bg_class_priors' AND retired_at IS NULL`,
      )
      await expect(client.query(migration)).rejects.toThrow(
        'migration 604 refuses unknown current class-prior digest specification',
      )
      const current = await client.query(
        `SELECT count(*)::int AS count
         FROM asset_output_digest_specs WHERE retired_at IS NULL`,
      )
      expect(current.rows[0].count).toBe(2)
    } finally {
      await client.end()
    }
  })

  it('rejects lifetime-count description drift before retiring either spec', async () => {
    const client = await connectPrepared()
    try {
      await client.query(
        `UPDATE asset_registry SET english_description = english_description || ' drift'
         WHERE asset_id = 'bg_class_lifetime_counts'`,
      )
      await expect(client.query(migration)).rejects.toThrow(
        'migration 604 refuses unknown bg_class_lifetime_counts registry contract',
      )
      const current = await client.query(
        `SELECT count(*)::int AS count
         FROM asset_output_digest_specs WHERE retired_at IS NULL`,
      )
      expect(current.rows[0].count).toBe(2)
    } finally {
      await client.end()
    }
  })

  it('rolls all changes back with the runner-owned transaction', async () => {
    const client = await connectPrepared()
    try {
      await client.query('BEGIN')
      await client.query(migration)
      await client.query('ROLLBACK')
      const current = await client.query(
        `SELECT asset_id, spec_sha256 FROM asset_output_digest_specs
         WHERE retired_at IS NULL ORDER BY asset_id`,
      )
      expect(current.rows).toEqual([
        { asset_id: 'bg_class_lifetime_counts', spec_sha256: OLD_SPEC_SHA },
        { asset_id: 'bg_class_priors', spec_sha256: OLD_SPEC_SHA },
      ])
      const floors = await client.query(
        `SELECT asset_id, target_floor FROM asset_registry ORDER BY asset_id`,
      )
      expect(floors.rows).toEqual([
        { asset_id: 'bg_class_lifetime_counts', target_floor: 0 },
        { asset_id: 'bg_class_priors', target_floor: null },
        { asset_id: 'bg_ghatana', target_floor: null },
      ])
    } finally {
      await client.end()
    }
  })
})
