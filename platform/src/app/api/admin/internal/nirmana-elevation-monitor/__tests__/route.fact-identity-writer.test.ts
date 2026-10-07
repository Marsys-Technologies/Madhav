// @vitest-environment node
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import type { NirmanaRegistryContractRow } from '@/lib/nirmana-elevation/definitions'

vi.mock('server-only', () => ({}))

const { verifyOidcTokenMock } = vi.hoisted(() => ({ verifyOidcTokenMock: vi.fn() }))
vi.mock('@/lib/auth/oidc', () => ({ verifyOidcToken: verifyOidcTokenMock }))

const clientQueryMock = vi.fn()
const clientReleaseMock = vi.fn()
const connectMock = vi.fn()
const insertQueryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({
  getPool: () => Promise.resolve({ connect: (...args: unknown[]) => connectMock(...args) }),
  query: (...args: unknown[]) => insertQueryMock(...args),
}))

const releaseMock = vi.fn()
vi.mock('@/lib/nirmana-elevation/release', () => ({ loadNirmanaReleaseStatus: () => releaseMock() }))

const schedulerOidcToken = 'scheduler-oidc-token'
const schedulerServiceAccount = 'amjis-nirmana-monitor@madhav-astrology.iam.gserviceaccount.com'
const sourceObservedAt = new Date().toISOString()

function request(headers: Record<string, string> = {}): Request {
  return new Request('https://madhav.example/api/admin/internal/nirmana-elevation-monitor', { method: 'POST', headers })
}

function registryRow(): NirmanaRegistryContractRow {
  return {
    asset_id: 'bg_reference', layer: 'brahmagyan', depends_on: [], sort_order: 1,
    scope: 'global', asset_kind: 'data', catalog_status: 'CURRENT', is_active: true,
    has_writer: true, target_table: 'bg_reference_rows',
    count_sql: 'SELECT count(*) FROM bg_reference_rows', integrity_check_sql: null,
    health_probe: null, natural_key_partition: null, superseded_by: null,
    data_disposition: null, dead_flag: null, sanskrit_name: null,
    english_name: 'Reference data', english_description: 'Authoritative reference values.',
  }
}

function successfulSources({
  definitions = [], receipts = [], labels = [], runs = [], observedAt = sourceObservedAt, registryRows = [registryRow()],
}: {
  definitions?: unknown[]
  receipts?: unknown[]
  labels?: unknown[]
  runs?: unknown[]
  observedAt?: string
  registryRows?: unknown[]
} = {}) {
  clientQueryMock.mockImplementation((statement: unknown) => {
    const sql = String(statement)
    if (/^BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY$/i.test(sql)) return Promise.resolve({ rows: [], rowCount: null })
    if (/^(COMMIT|ROLLBACK)$/i.test(sql)) return Promise.resolve({ rows: [], rowCount: null })
    if (sql.includes('transaction_timestamp()')) return Promise.resolve({ rows: [{ source_observed_at: observedAt }], rowCount: 1 })
    if (sql.includes('FROM asset_registry')) return Promise.resolve({ rows: registryRows, rowCount: registryRows.length })
    if (sql.includes('FROM nirmana_evidence.nirmana_elevation_campaign_definitions')) return Promise.resolve({ rows: definitions, rowCount: definitions.length })
    if (sql.includes('FROM nirmana_evidence.nirmana_elevation_campaign_events')) return Promise.resolve({ rows: receipts, rowCount: receipts.length })
    if (sql.includes('FROM nirmana_evidence.nirmana_elevation_asset_labels')) return Promise.resolve({ rows: labels, rowCount: labels.length })
    if (sql.includes('FROM asset_throughput')) return Promise.resolve({ rows: [], rowCount: 0 })
    if (sql.includes('FROM build_run_assets')) return Promise.resolve({ rows: [], rowCount: 0 })
    if (sql.includes('FROM build_substep_progress')) return Promise.resolve({ rows: [], rowCount: 0 })
    if (sql.includes('FROM build_runs')) return Promise.resolve({ rows: runs, rowCount: runs.length })
    throw new Error(`Unexpected client query: ${sql}`)
  })
  insertQueryMock.mockImplementation((statement: unknown, params?: unknown[]) => {
    const sql = String(statement)
    if (!sql.includes('INSERT INTO nirmana_elevation_monitor_observations')) throw new Error(`Unexpected pooled query: ${sql}`)
    const sourceObservedAt = typeof params?.[11] === 'string' ? params[11] : null
    const freshnessDeadlineAt = sourceObservedAt === null
      ? null
      : new Date(Date.parse(sourceObservedAt) + 15 * 60 * 1000).toISOString()
    return Promise.resolve({ rows: [{
      id: 'a8c01784-865f-4880-b91b-0988ab7f31de', observed_at: sourceObservedAt,
      status: params?.[0], affected_asset_ids: params?.[1], current_definition_sha256: params?.[2],
      candidate_definition_sha256: params?.[3], registry_identity_sha256: params?.[4],
      registry_contract_sha256: params?.[5], candidate_catalogue_sha256: params?.[6],
      selected_catalogue_sha256: params?.[7], runtime_sha256: params?.[8], release_sha256: params?.[9],
      source_state: params?.[10], source_observed_at: params?.[11], source_age_seconds: params?.[12],
      freshness_state: params?.[13], freshness_deadline_at: freshnessDeadlineAt, runtime_liveness: params?.[14],
      release_state: params?.[15], release_observed_at: params?.[16], release_age_seconds: params?.[17],
      public_detail: params?.[18], source_error_code: params?.[19],
    }], rowCount: 1 })
  })
}

/**
 * ga_fact_identity after migration 1333 — the monitor ROUTE over the production-shaped registry (read 2026-10-05, after 1262) transformed to the post-1333 shape.
 * N-141 (the writer-less exclusion) is REMOVED, so ga_fact_identity is an ordinary build asset: it is no longer named in `excluded_staged_candidates`, the reading is not
 * source_unavailable, and a definition frozen before the asset reads as drift (not in_sync). The pre-1333 registry with the rule gone fails closed (the one-deploy window).
 */
const production = JSON.parse(readFileSync(path.resolve(__dirname, '../../../../../../lib/nirmana-elevation/__tests__/fixtures/production_asset_registry_2026_10_05.json'), 'utf8')) as { rows: NirmanaRegistryContractRow[] }
const UPSTREAM = ['ga_ayurdaya', 'ga_condition', 'ga_dashas', 'ga_nakshatra', 'ga_panchanga', 'ga_positions', 'ga_sade_sati', 'ga_sensitive', 'ga_sensitive_degree', 'ga_strength', 'ga_structural']
const post1333 = () => production.rows.map((r) => {
  if (r.asset_id === 'ga_fact_identity') return { ...r, has_writer: true, depends_on: [...UPSTREAM] }
  if (r.asset_id === 'bo_pratijna') return { ...r, depends_on: [...(r.depends_on ?? []), 'ga_fact_identity'] }
  return r
})
const STAGED = ['ka_gochara_v3_century_materialize', 'ka_gochara_v4_41_candidate', 'ka_gochara_v5']

describe('POST /api/admin/internal/nirmana-elevation-monitor — ga_fact_identity after migration 1333', () => {
  beforeEach(() => {
    vi.resetModules()
    clientQueryMock.mockReset()
    clientReleaseMock.mockReset()
    connectMock.mockReset().mockResolvedValue({ query: clientQueryMock, release: clientReleaseMock })
    insertQueryMock.mockReset()
    releaseMock.mockReset().mockResolvedValue({
      release: {
        main_sha: 'a'.repeat(40), deployed_sha: 'a'.repeat(40),
        deployed_revision: 'amjis-web-01705-abc', production_in_sync: true, observed_at: sourceObservedAt,
      },
      sources: [
        { source_id: 'github_main', state: 'fresh', observed_at: sourceObservedAt, age_seconds: 0 },
        { source_id: 'cloud_run_web', state: 'fresh', observed_at: sourceObservedAt, age_seconds: 0 },
        { source_id: 'artifact_registry_commit', state: 'fresh', observed_at: sourceObservedAt, age_seconds: 0 },
      ],
      gaps: [],
    })
    verifyOidcTokenMock.mockReset().mockResolvedValue({
      email: schedulerServiceAccount,
      sub: 'scheduler-subject',
    })
  })

  it('the post-1333 registry reads WITHOUT source_unavailable, and ga_fact_identity is NOT listed as an excluded candidate (only the three staged ids are)', async () => {
    const info = vi.spyOn(console, 'info').mockImplementation(() => undefined)
    successfulSources({ registryRows: post1333() })
    const { POST } = await import('../route')
    const response = await POST(request({ Authorization: `Bearer ${schedulerOidcToken}` }))
    const body = await response.json()
    expect(response.status).toBe(200)
    expect(body.status).not.toBe('source_unavailable')
    expect(body.excluded_staged_candidates.map((e: { asset_id: string }) => e.asset_id)).toEqual(STAGED)
    const logged = info.mock.calls.filter(([message]) => String(message).includes('staged candidate excluded'))
    expect(logged.map(([, detail]) => (detail as { asset_id: string }).asset_id)).toEqual(STAGED)
    const registrySql = clientQueryMock.mock.calls.map(([sql]) => String(sql)).find((sql) => sql.includes('FROM asset_registry')) ?? ''
    expect(registrySql).toContain('has_non_test_runtime_evidence')
    expect(registrySql).not.toContain('ga_fact_identity')
    info.mockRestore()
  })

  it('the one-deploy window: the pre-1333 registry (writer-less, active) with the rule gone reads source_unavailable (fails closed), never a quiet reading', async () => {
    const info = vi.spyOn(console, 'info').mockImplementation(() => undefined)
    const error = vi.spyOn(console, 'error').mockImplementation(() => undefined)
    successfulSources({ registryRows: production.rows })
    const { POST } = await import('../route')
    const body = await (await POST(request({ Authorization: `Bearer ${schedulerOidcToken}` }))).json()
    expect(body.status).toBe('source_unavailable')
    expect(body.excluded_staged_candidates.map((e: { asset_id: string }) => e.asset_id)).not.toContain('ga_fact_identity')
    info.mockRestore(); error.mockRestore()
  })
})
