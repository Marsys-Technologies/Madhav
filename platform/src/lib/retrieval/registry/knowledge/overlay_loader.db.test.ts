import { randomUUID } from 'node:crypto'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import { Pool } from 'pg'
import type { CapabilityKnowledgeSnapshot } from './types'
import { loadChartCapabilityOverlay, type OverlayQueryExecutor, type OverlayQueryRow } from './overlay_loader'

const DATABASE_URL = process.env.PURNA_ANVESANA_OVERLAY_TEST_DATABASE_URL
const run = DATABASE_URL ? describe : describe.skip
const claimHash = '44333a746758f9a71288524273a4941071391f60ec753062d5295fafba6dcad7'
const chartId = '482012f1-710e-4a25-994a-93821f5871aa'
const oldBuildId = '11111111-1111-4111-8111-111111111111'
const currentBuildId = '22222222-2222-4222-8222-222222222222'
const schema = `purna_overlay_${randomUUID().replaceAll('-', '')}`

function assertDisposableDatabase(url: string): void {
  const parsed = new URL(url)
  if (!['localhost', '127.0.0.1', '::1'].includes(parsed.hostname)) {
    throw new Error('PURNA_ANVESANA_OVERLAY_TEST_DATABASE_URL must target localhost')
  }
  if (!parsed.pathname.endsWith('/purna_overlay_test')) {
    throw new Error('PURNA_ANVESANA_OVERLAY_TEST_DATABASE_URL must target database purna_overlay_test')
  }
}

function migration(relativePath: string): string {
  return readFileSync(path.join(process.cwd(), relativePath), 'utf8')
}

const snapshot = (expectedHash = claimHash): CapabilityKnowledgeSnapshot => ({
  schema_version: '2.3.0', compatibility_version: 'planner-scu-v2', generated_at: '2026-09-15T00:00:00.000Z',
  content_hash: 'sha256:overlay-db-fixture', source_catalog_fingerprint: 'sha256:catalog',
  semantic_review_fingerprint: 'sha256:review', producer_contract_fingerprint: 'sha256:producer',
  edges: [], concept_universe: [], producer_semantic_bindings: [],
  census: {
    runtime_descriptors: 1, addressable_descriptors: 1, excluded_descriptors: 0, semantic_capabilities: 1,
    editorial_scus: 1, derived_scus: 0, executable_bindings: 1, unavailable_bindings: 0,
    publicly_named_bindings: 0, reviewed_pagination_bindings: 0, reviewed_pagination_dispositions: 1,
    reviewed_paginated_descriptors: 0, exhaustible_reviewed_descriptors: 0, non_exhaustible_descriptors: 0,
    reviewed_route_descriptors: 1, reviewed_public_descriptors: 0, reviewed_nonpublic_descriptors: 1,
    producer_output_claims: 1, reviewed_output_claims: 1, typed_concepts: 0, unbound_concepts: 0,
    isolated_scus: 1, graph_components: 1, dispositioned_isolated_scus: 1, unresolved_isolated_scus: 0,
    producer_semantic_bindings: 0, directly_served_producer_outputs: 0, support_only_producer_bindings: 0,
    unbound_active_producers: 0, undispositioned_producer_scus: 0, undispositioned_gaps: 0, exclusions: [],
  },
  scus: [{
    scu_id: 'scu.overlay.db', version: 1, label: 'Overlay DB', description: 'Disposable overlay database fixture.',
    kind: 'datum', domains: ['health'], concepts: [], intents: ['retrieve'], horizons: ['natal'], scope: 'chart',
    inputs: ['chart_id'], outputs: ['medical_mapping'], primary_binding_uri: 'marsys://tool/L1/overlay_db',
    provenance_requirements: ['chart_id', 'build_id'], freshness_policy: 'active build only', entitlement: 'native',
    safety_notes: ['Read-only fixture.'], known_gaps: [], editorial: true,
    producer_output_claims: [{
      asset_id: 'bg_sign_medical', component: 'bg_sign_medical', output_digest_spec_sha256: expectedHash,
      disposition: 'reviewed_output', evidence: 'migration 1034 fixture',
    }],
    bindings: [{
      binding_id: 'registry:marsys://tool/L1/overlay_db', kind: 'registry_capability', relation: 'primary',
      capability_uri: 'marsys://tool/L1/overlay_db', input_contract: {}, output_contract: {}, pagination: 'none', executable: true,
    }],
    source_descriptor_uris: ['marsys://tool/L1/overlay_db'], editorial_method: 'authored_declaration',
    editorial_sources: [{ source_ref: 'fixture', source_fields: ['description'] }], concept_bindings: [], gap_dispositions: [],
    graph_disposition: { status: 'isolated_dispositioned', rationale: 'Disposable test fixture.', source_refs: ['fixture'] },
    producer_semantic_disposition: { status: 'linked', asset_ids: ['bg_sign_medical'], rationale: 'Fixture link.', source_refs: ['fixture'] },
  }],
})

run('chart capability overlay disposable schema replay', () => {
  let admin: Pool
  let scoped: Pool
  let query: OverlayQueryExecutor

  beforeAll(async () => {
    assertDisposableDatabase(DATABASE_URL!)
    admin = new Pool({ connectionString: DATABASE_URL!, max: 1 })
    await admin.query(`CREATE SCHEMA ${schema}`)
    scoped = new Pool({
      connectionString: DATABASE_URL!, max: 1,
      options: `-c search_path=${schema}`,
    })
    query = async (sql, params) => ({ rows: (await scoped.query<OverlayQueryRow>(sql, params)).rows })

    await scoped.query(`
      CREATE TABLE charts (
        id uuid PRIMARY KEY, birth_date date, birth_time time, birth_lat numeric, birth_lng numeric,
        birth_place text, timezone_id text, name text, subject_name text, preferred_name text
      );
      CREATE TABLE asset_registry (
        asset_id text PRIMARY KEY, depends_on jsonb, natural_key_partition text, health_probe text,
        integrity_check_sql text, target_floor integer, asset_kind text, asset_type text, scope text,
        has_writer boolean, is_active boolean, target_table text
      );
      CREATE TABLE asset_throughput (asset_id text PRIMARY KEY);
    `)
    const digestSql = migration('supabase/migrations/598_nirmana_output_digest_specs.sql')
      + migration('migrations/1034_nirmana_purna_anvesana_wave1_output_digest_specs.sql')
    const assetIds = [...digestSql.matchAll(/'([a-z0-9_]+)'\s*,\s*'[a-f0-9]{64}'/g)].map((match) => match[1]!)
    await scoped.query(
      'INSERT INTO asset_registry(asset_id) SELECT unnest($1::text[]) ON CONFLICT DO NOTHING',
      [[...new Set(assetIds)]],
    )
    await scoped.query(migration('supabase/migrations/171_build_runs.sql'))
    await scoped.query(migration('supabase/migrations/596_nirmana_provenance_receipts.sql'))
    await scoped.query(migration('supabase/migrations/598_nirmana_output_digest_specs.sql'))
    await scoped.query(migration('migrations/1034_nirmana_purna_anvesana_wave1_output_digest_specs.sql'))

    await scoped.query('INSERT INTO charts(id, name) VALUES ($1, $2)', [chartId, 'Disposable Overlay'])
    await scoped.query(`
      INSERT INTO build_runs(id, chart_id, scope, action, state, plan, triggered_by, ended_at)
      VALUES
        ($1, $3, 'asset', 'build', 'completed', '{}'::jsonb, 'test', '2026-09-14T00:00:00Z'),
        ($2, $3, 'asset', 'build', 'completed', '{}'::jsonb, 'test', '2026-09-15T00:00:00Z')
    `, [oldBuildId, currentBuildId, chartId])
    await scoped.query(`
      INSERT INTO asset_provenance_receipts
        (asset_id, chart_id, partition_key, receipt_version, receipt_state, build_id, output_digest_spec_sha256, unknown_reasons, observed_at)
      VALUES
        ('bg_sign_medical', $1, 'old-partition', 'old', 'proven', $2, $4, '[]', '2026-09-14T00:00:00Z'),
        ('bg_sign_medical', $1, 'current-partition', 'current', 'proven', $3, $4, '[]', '2026-09-15T00:00:00Z'),
        ('bg_sign_medical', NULL, 'global', 'global', 'unknown', NULL, $4, '["global-not-selected"]', '2026-09-15T00:00:00Z')
    `, [chartId, oldBuildId, currentBuildId, claimHash])
    await scoped.query(`
      INSERT INTO asset_freshness(asset_id, chart_id, partition_key, freshness_state, reasons, receipt_version, observed_at)
      VALUES
        ('bg_sign_medical', $1, 'old-partition', 'fresh', '[]', 'old', '2026-09-14T00:00:00Z'),
        ('bg_sign_medical', $1, 'current-partition', 'fresh', '[]', 'current', '2026-09-15T00:00:00Z'),
        ('bg_sign_medical', NULL, 'global', 'unknown', '["global-not-selected"]', 'global', '2026-09-15T00:00:00Z')
    `, [chartId])
  }, 30_000)

  afterAll(async () => {
    await scoped?.end()
    if (admin) {
      await admin.query(`DROP SCHEMA IF EXISTS ${schema} CASCADE`)
      await admin.end()
    }
  })

  it('selects only the latest completed chart build despite stale/global rows', async () => {
    const overlay = await loadChartCapabilityOverlay(snapshot(), chartId, query)
    expect(overlay.build_id).toBe(currentBuildId)
    expect(overlay.availability[0]).toMatchObject({
      state: 'available',
      asset_receipts: [expect.objectContaining({ state: 'passed', build_id: currentBuildId })],
    })
  })

  it('falls back to global evidence only when the active chart receipt is absent', async () => {
    await scoped.query("DELETE FROM asset_provenance_receipts WHERE partition_key='current-partition'")
    await scoped.query("UPDATE asset_provenance_receipts SET receipt_state='proven' WHERE partition_key='global'")
    await scoped.query("UPDATE asset_freshness SET freshness_state='fresh', reasons='[]' WHERE partition_key='global'")
    const overlay = await loadChartCapabilityOverlay(snapshot(), chartId, query)
    expect(overlay.availability[0]).toMatchObject({
      state: 'available',
      asset_receipts: [expect.objectContaining({ state: 'passed', build_id: null })],
    })
  })

  it('fails closed for absent active/global evidence and for a mismatched reviewed specification', async () => {
    await scoped.query("DELETE FROM asset_provenance_receipts WHERE partition_key='global'")
    expect((await loadChartCapabilityOverlay(snapshot(), chartId, query)).availability[0]).toMatchObject({ state: 'dark' })

    await scoped.query(`
      INSERT INTO asset_provenance_receipts
        (asset_id, chart_id, partition_key, receipt_version, receipt_state, build_id, output_digest_spec_sha256, unknown_reasons)
      VALUES ('bg_sign_medical', $1, 'current-reseed', 'current-2', 'proven', $2, $3, '[]')
    `, [chartId, currentBuildId, claimHash])
    await scoped.query(`
      INSERT INTO asset_freshness(asset_id, chart_id, partition_key, freshness_state, reasons, receipt_version)
      VALUES ('bg_sign_medical', $1, 'current-reseed', 'fresh', '[]', 'current-2')
    `, [chartId])
    expect((await loadChartCapabilityOverlay(snapshot('b'.repeat(64)), chartId, query)).availability[0])
      .toMatchObject({ state: 'incompatible', available_binding_ids: [] })
  })
})
