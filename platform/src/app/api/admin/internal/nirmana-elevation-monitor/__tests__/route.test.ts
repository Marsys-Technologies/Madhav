// @vitest-environment node
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { NirmanaRegistryContractRow } from '@/lib/nirmana-elevation/definitions'

vi.mock('server-only', () => ({}))

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

const releaseMock = vi.fn()
vi.mock('@/lib/nirmana-elevation/release', () => ({ loadNirmanaReleaseStatus: () => releaseMock() }))

const secret = 'scheduler-secret'

function request(headers: Record<string, string> = {}): Request {
  return new Request('https://madhav.example/api/admin/internal/nirmana-elevation-monitor', {
    method: 'POST',
    headers,
  })
}

function registryRow(): NirmanaRegistryContractRow {
  return {
    asset_id: 'bg_reference',
    layer: 'brahmagyan',
    depends_on: [],
    sort_order: 1,
    scope: 'global',
    asset_kind: 'data',
    catalog_status: 'CURRENT',
    is_active: true,
    has_writer: true,
    target_table: 'bg_reference_rows',
    count_sql: 'SELECT count(*) FROM bg_reference_rows',
    integrity_check_sql: null,
    health_probe: null,
    natural_key_partition: null,
    superseded_by: null,
    data_disposition: null,
    dead_flag: null,
    sanskrit_name: null,
    english_name: 'Reference data',
    english_description: 'Authoritative reference values.',
  }
}

function successfulSources({
  definitions = [],
  receipts = [],
  labels = [],
}: {
  definitions?: unknown[]
  receipts?: unknown[]
  labels?: unknown[]
} = {}) {
  queryMock.mockImplementation((statement: unknown, params?: unknown[]) => {
    const sql = String(statement)
    if (sql.includes('FROM asset_registry')) return Promise.resolve({ rows: [registryRow()], rowCount: 1 })
    if (sql.includes('FROM nirmana_elevation_campaign_definitions')) return Promise.resolve({ rows: definitions, rowCount: definitions.length })
    if (sql.includes('FROM nirmana_elevation_campaign_events')) return Promise.resolve({ rows: receipts, rowCount: receipts.length })
    if (sql.includes('FROM nirmana_elevation_asset_labels')) return Promise.resolve({ rows: labels, rowCount: labels.length })
    if (sql.includes('FROM asset_throughput')) return Promise.resolve({ rows: [], rowCount: 0 })
    if (sql.includes('FROM build_runs')) return Promise.resolve({ rows: [], rowCount: 0 })
    if (sql.includes('FROM build_run_assets')) return Promise.resolve({ rows: [], rowCount: 0 })
    if (sql.includes('FROM build_substep_progress')) return Promise.resolve({ rows: [], rowCount: 0 })
    if (sql.includes('INSERT INTO nirmana_elevation_monitor_observations')) {
      return Promise.resolve({
        rows: [{
          id: 'a8c01784-865f-4880-b91b-0988ab7f31de',
          observed_at: '2026-08-26T09:00:00.000Z',
          status: params?.[0],
          affected_asset_ids: params?.[1],
          current_definition_sha256: params?.[2],
          candidate_definition_sha256: params?.[3],
          registry_identity_sha256: params?.[4],
          registry_contract_sha256: params?.[5],
          candidate_catalogue_sha256: params?.[6],
          selected_catalogue_sha256: params?.[7],
          runtime_sha256: params?.[8],
          release_sha256: params?.[9],
          public_detail: params?.[10],
          source_error_code: params?.[11],
        }],
        rowCount: 1,
      })
    }
    throw new Error(`Unexpected query: ${sql}`)
  })
}

describe('POST /api/admin/internal/nirmana-elevation-monitor', () => {
  beforeEach(() => {
    vi.resetModules()
    queryMock.mockReset()
    releaseMock.mockReset().mockResolvedValue({
      release: {
        main_sha: 'a'.repeat(40),
        deployed_sha: 'a'.repeat(40),
        deployed_revision: 'amjis-web-01705-abc',
        production_in_sync: true,
        observed_at: '2026-08-26T09:00:00.000Z',
      },
      sources: [],
      gaps: [],
    })
    process.env.MARSYS_CRON_SECRET = secret
  })

  it('rejects an unauthenticated request before reading or recording program state', async () => {
    const { POST } = await import('../route')

    const response = await POST(request())

    expect(response.status).toBe(401)
    expect(response.headers.get('Cache-Control')).toBe('no-store')
    expect(queryMock).not.toHaveBeenCalled()
    expect(releaseMock).not.toHaveBeenCalled()
  })

  it.each([
    ['scheduler header', { 'X-Marsys-Cron-Secret': secret }],
    ['bearer fallback', { Authorization: `Bearer ${secret}` }],
  ])('records one no-store observation with the %s', async (_label, headers) => {
    successfulSources()
    const { POST } = await import('../route')

    const response = await POST(request(headers))
    const body = await response.json()

    expect(response.status).toBe(200)
    expect(response.headers.get('Cache-Control')).toBe('no-store')
    expect(body).toEqual({
      ok: true,
      observation_id: 'a8c01784-865f-4880-b91b-0988ab7f31de',
      status: 'baseline_missing',
    })

    const statements = queryMock.mock.calls.map(([sql]) => String(sql))
    expect(statements.join('\n')).toContain('FROM asset_registry')
    expect(statements.join('\n')).toContain('FROM nirmana_elevation_campaign_definitions')
    expect(statements.join('\n')).toContain('FROM nirmana_elevation_campaign_events')
    expect(statements.join('\n')).toContain('FROM nirmana_elevation_asset_labels')
    expect(statements.join('\n')).toContain('FROM asset_throughput')
    expect(statements.join('\n')).toContain('FROM build_runs')
    expect(statements.join('\n')).toContain('FROM build_run_assets')
    expect(statements.join('\n')).toContain('FROM build_substep_progress')
    const insertStatements = statements.filter((sql) => /^\s*INSERT\b/i.test(sql))
    expect(insertStatements).toHaveLength(1)
    expect(insertStatements[0]).toContain('INSERT INTO nirmana_elevation_monitor_observations')

    const mutationSql = statements.filter((sql) => /^\s*(INSERT|UPDATE|DELETE|TRUNCATE|MERGE)\b/i.test(sql)).join('\n')
    expect(mutationSql).not.toContain('nirmana_elevation_campaign_definitions')
    expect(mutationSql).not.toContain('nirmana_elevation_campaign_events')
    expect(mutationSql).not.toContain('nirmana_elevation_asset_labels')
    expect(mutationSql).not.toMatch(/\b(build_runs|build_run_assets|build_substep_progress|asset_throughput)\b/)
  })

  it('records a sanitized source-unavailable observation when a read fails but the observation table remains writable', async () => {
    const log = vi.spyOn(console, 'error').mockImplementation(() => undefined)
    successfulSources()
    queryMock.mockImplementationOnce(() => Promise.reject(new Error('password=super-secret host=private-db.internal')))
    const { POST } = await import('../route')

    const response = await POST(request({ 'X-Marsys-Cron-Secret': secret }))
    const body = await response.json()

    expect(response.status).toBe(200)
    expect(body.status).toBe('source_unavailable')
    const insertCall = queryMock.mock.calls.find(([sql]) => String(sql).includes('INSERT INTO nirmana_elevation_monitor_observations'))
    expect(insertCall).toBeDefined()
    expect(insertCall?.[1]).toEqual(expect.arrayContaining([
      'source_unavailable',
      'Authoritative source is unavailable.',
      'NIRMANA_SOURCE_UNAVAILABLE',
    ]))
    expect(JSON.stringify(insertCall)).not.toContain('super-secret')
    expect(JSON.stringify(insertCall)).not.toContain('private-db.internal')
    expect(log).toHaveBeenCalledWith(
      '[nirmana-elevation] monitor source read failed',
      expect.objectContaining({ cause: expect.any(Error) }),
    )
  })

  it('derives the selected catalogue digest from label content instead of trusting a stored digest stamp', async () => {
    const { buildNirmanaBaselineCandidate } = await import('@/lib/nirmana-elevation/monitor')
    const candidate = buildNirmanaBaselineCandidate([registryRow()])
    successfulSources({
      definitions: [{
        definition_revision: 'ntap-v1',
        definition_status: 'frozen',
        manifest: candidate.manifest,
        manifest_sha256: candidate.manifest_sha256,
      }],
      receipts: [{ catalogue_revision: 'labels-v1', catalogue_sha256: candidate.catalogue_sha256 }],
      labels: [{
        asset_id: 'bg_reference',
        sanskrit_name: null,
        english_name: 'Tampered label content',
        description: 'Authoritative reference values.',
        legacy_aliases: [],
        source_ref: 'asset_registry:bg_reference',
        label_digest: candidate.catalogue_sha256,
      }],
    })
    const { POST } = await import('../route')

    const response = await POST(request({ 'X-Marsys-Cron-Secret': secret }))
    const body = await response.json()

    expect(response.status).toBe(200)
    expect(body.status).toBe('label_refresh_required')
  })
})
