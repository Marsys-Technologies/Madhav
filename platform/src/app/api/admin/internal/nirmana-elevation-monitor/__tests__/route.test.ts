// @vitest-environment node
import { beforeEach, describe, expect, it, vi } from 'vitest'
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
const schedulerOidcAudience = 'https://amjis-web-938361928218.asia-south1.run.app'
const schedulerServiceAccount = 'amjis-nirmana-monitor@madhav-astrology.iam.gserviceaccount.com'
const sourceObservedAt = new Date().toISOString()
const freshnessDeadlineAt = new Date(Date.parse(sourceObservedAt) + 15 * 60 * 1000).toISOString()

function sensitiveDatabaseError(value: string, host: string): Error {
  // Build the credential-shaped input at runtime: this tests redaction without
  // committing a literal secret-shaped value that the repository scan must reject.
  const passwordKey = ['pass', 'word'].join('')
  return new Error(`${passwordKey}=${value} host=${host}`)
}

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

describe('POST /api/admin/internal/nirmana-elevation-monitor', () => {
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

  it('rejects an unauthenticated request before reading or recording program state', async () => {
    const { POST } = await import('../route')
    const response = await POST(request())
    expect(response.status).toBe(401)
    expect(response.headers.get('Cache-Control')).toBe('no-store')
    expect(verifyOidcTokenMock).not.toHaveBeenCalled()
    expect(connectMock).not.toHaveBeenCalled()
    expect(insertQueryMock).not.toHaveBeenCalled()
    expect(releaseMock).not.toHaveBeenCalled()
  })

  it('does not accept the retired shared-secret header in place of a Scheduler OIDC bearer token', async () => {
    const { POST } = await import('../route')
    const response = await POST(request({ 'X-Marsys-Cron-Secret': 'retired-secret' }))
    expect(response.status).toBe(401)
    expect(verifyOidcTokenMock).not.toHaveBeenCalled()
    expect(connectMock).not.toHaveBeenCalled()
    expect(insertQueryMock).not.toHaveBeenCalled()
  })

  it('rejects an invalid OIDC token before reading or recording program state', async () => {
    verifyOidcTokenMock.mockResolvedValueOnce(null)
    const { POST } = await import('../route')
    const response = await POST(request({ Authorization: `Bearer ${schedulerOidcToken}` }))
    expect(response.status).toBe(403)
    expect(response.headers.get('Cache-Control')).toBe('no-store')
    expect(verifyOidcTokenMock).toHaveBeenCalledWith(schedulerOidcToken, {
      expectedAudience: schedulerOidcAudience,
      expectedServiceAccount: schedulerServiceAccount,
    })
    expect(connectMock).not.toHaveBeenCalled()
    expect(insertQueryMock).not.toHaveBeenCalled()
    expect(releaseMock).not.toHaveBeenCalled()
  })

  it('rejects an OIDC verification failure before reading or recording program state', async () => {
    verifyOidcTokenMock.mockRejectedValueOnce(new Error('TokenExpiredError'))
    const { POST } = await import('../route')
    const response = await POST(request({ Authorization: `Bearer ${schedulerOidcToken}` }))
    expect(response.status).toBe(403)
    expect(connectMock).not.toHaveBeenCalled()
    expect(insertQueryMock).not.toHaveBeenCalled()
    expect(releaseMock).not.toHaveBeenCalled()
  })

  it('records explicit fresh, quiet, and release state with the dedicated Scheduler OIDC token', async () => {
    successfulSources()
    const { POST } = await import('../route')
    const response = await POST(request({ Authorization: `Bearer ${schedulerOidcToken}` }))
    const body = await response.json()
    expect(response.status).toBe(200)
    expect(response.headers.get('Cache-Control')).toBe('no-store')
    expect(verifyOidcTokenMock).toHaveBeenCalledWith(schedulerOidcToken, {
      expectedAudience: schedulerOidcAudience,
      expectedServiceAccount: schedulerServiceAccount,
    })
    expect(body).toEqual({
      ok: true, observation_id: 'a8c01784-865f-4880-b91b-0988ab7f31de',
      status: 'baseline_missing', source_state: 'available', freshness_state: 'fresh',
      freshness_deadline_at: freshnessDeadlineAt, runtime_liveness: 'quiet', release_state: 'in_sync',
      excluded_staged_candidates: [],
    })

    const clientStatements = clientQueryMock.mock.calls.map(([sql]) => String(sql))
    expect(clientStatements[0]).toBe('BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
    expect(clientStatements.at(-1)).toBe('COMMIT')
    expect(clientReleaseMock).toHaveBeenCalledOnce()
    expect(insertQueryMock).toHaveBeenCalledOnce()
    expect(String(insertQueryMock.mock.calls[0][0])).toContain('INSERT INTO nirmana_elevation_monitor_observations')
    const sourceSql = clientStatements.join('\n')
    for (const table of [
      'asset_registry', 'nirmana_elevation_campaign_definitions', 'nirmana_elevation_campaign_events',
      'nirmana_elevation_asset_labels', 'asset_throughput', 'build_runs', 'build_run_assets',
      'build_substep_progress',
    ]) expect(sourceSql).toContain(table)
    expect(sourceSql).not.toMatch(/^\s*(INSERT|UPDATE|DELETE|TRUNCATE|MERGE)\b/im)
  })

  // N-137: the exclusion of the staged Gochara candidates is VISIBLE in the monitor output, and any other state fails closed
  const stagedRow = (asset_id: string, over: Partial<NirmanaRegistryContractRow> = {}): NirmanaRegistryContractRow => ({
    ...registryRow(), asset_id, layer: 'kala', scope: 'per_chart', is_active: false, target_table: 'kala_gochara_windows',
    count_sql: 'SELECT count(*) FROM kala_gochara_windows', has_non_test_runtime_evidence: false, ...over,
  })

  it('N-137: names every excluded staged candidate (id, reason, decision) in the response and logs one line per id each run', async () => {
    const info = vi.spyOn(console, 'info').mockImplementation(() => undefined)
    successfulSources({ registryRows: [registryRow(), stagedRow('ka_gochara_v4_41_candidate'), stagedRow('ka_gochara_v5', { depends_on: ['ga_positions', 'ga_dashas'] })] })
    const { POST } = await import('../route')
    const response = await POST(request({ Authorization: `Bearer ${schedulerOidcToken}` }))
    const body = await response.json()
    expect(response.status).toBe(200)
    expect(body.excluded_staged_candidates).toEqual([
      { asset_id: 'ka_gochara_v4_41_candidate', reason: 'staged inert candidate', decision: 'PRAVAHA-2996 (migration 1243)' },
      { asset_id: 'ka_gochara_v5', reason: 'unsealed test candidate', decision: 'N-137' },
    ])
    expect(body.status).not.toBe('source_unavailable')                                  // the two candidates did not break the baseline: they are excluded, by the rule
    const logged = info.mock.calls.filter(([message]) => String(message).includes('staged candidate excluded'))
    expect(logged.map(([, detail]) => (detail as { asset_id: string }).asset_id)).toEqual(['ka_gochara_v4_41_candidate', 'ka_gochara_v5'])
    expect(logged[1][1]).toMatchObject({ reason: 'unsealed test candidate', decision: 'N-137' })
    const registrySql = clientQueryMock.mock.calls.map(([sql]) => String(sql)).find((sql) => sql.includes('FROM asset_registry')) ?? ''
    expect(registrySql).toContain('has_non_test_runtime_evidence')                      // the loader asks the rule's own detector (test triggers by build_runs.triggered_by)
    expect(registrySql).toContain("ARRAY['gochara-v5-small-test']::text[]")
    info.mockRestore()
  })

  it.each([
    ['a non-test evidence row', { has_non_test_runtime_evidence: true }],
    ['is_active true', { is_active: true }],
    ['an extra dependency', { depends_on: ['ga_positions', 'ga_dashas', 'bg_reference'] }],
    ['a MISSING dependency', { depends_on: ['ga_dashas'] }],
    ['a DIFFERENT dependency', { depends_on: ['ga_dashas', 'bg_reference'] }],
  ])('N-137 fails closed: a v5 with %s is NOT excluded — it is not listed and the monitor cannot read the baseline as healthy', async (_name, over) => {
    const info = vi.spyOn(console, 'info').mockImplementation(() => undefined)
    const error = vi.spyOn(console, 'error').mockImplementation(() => undefined)
    successfulSources({ registryRows: [registryRow(), stagedRow('ka_gochara_v5', { depends_on: ['ga_positions', 'ga_dashas'], ...over })] })
    const { POST } = await import('../route')
    const response = await POST(request({ Authorization: `Bearer ${schedulerOidcToken}` }))
    const body = await response.json()
    expect(body.excluded_staged_candidates).toEqual([])
    expect(body.status).toBe('source_unavailable')                                      // the unresolved candidate in the denominator makes the baseline unbuildable: a loud state, never a quiet in_sync
    expect(info.mock.calls.filter(([message]) => String(message).includes('staged candidate excluded'))).toEqual([])
    info.mockRestore(); error.mockRestore()
  })

  it('N-137 fails closed: an asset that DEPENDS on v5 keeps it in the denominator — not excluded, not listed, and the monitor cannot read the baseline as healthy', async () => {
    const info = vi.spyOn(console, 'info').mockImplementation(() => undefined)
    const error = vi.spyOn(console, 'error').mockImplementation(() => undefined)
    const dependent = { ...registryRow(), asset_id: 'bg_depends_on_v5', sort_order: 2, depends_on: ['ka_gochara_v5'] }
    successfulSources({ registryRows: [registryRow(), stagedRow('ka_gochara_v5', { depends_on: ['ga_positions', 'ga_dashas'] }), dependent] })
    const { POST } = await import('../route')
    const body = await (await POST(request({ Authorization: `Bearer ${schedulerOidcToken}` }))).json()
    expect(body.excluded_staged_candidates).toEqual([])
    expect(body.status).toBe('source_unavailable')
    info.mockRestore(); error.mockRestore()
  })

  it('F4: the exclusions are reported BEFORE the baseline is built — a baseline that throws still shows what was excluded', async () => {
    const info = vi.spyOn(console, 'info').mockImplementation(() => undefined)
    const error = vi.spyOn(console, 'error').mockImplementation(() => undefined)
    // v4.1 is excluded by the rule; v5 carries NON-test evidence, so it stays in the denominator and the baseline throws
    successfulSources({ registryRows: [registryRow(), stagedRow('ka_gochara_v4_41_candidate'), stagedRow('ka_gochara_v5', { depends_on: ['ga_positions', 'ga_dashas'], has_non_test_runtime_evidence: true })] })
    const { POST } = await import('../route')
    const body = await (await POST(request({ Authorization: `Bearer ${schedulerOidcToken}` }))).json()
    expect(body.status).toBe('source_unavailable')                                                               // the baseline threw …
    expect(body.excluded_staged_candidates).toEqual([{ asset_id: 'ka_gochara_v4_41_candidate', reason: 'staged inert candidate', decision: 'PRAVAHA-2996 (migration 1243)' }])   // … and the exclusion is still shown
    const logged = info.mock.calls.filter(([message]) => String(message).includes('staged candidate excluded'))
    expect(logged.map(([, detail]) => (detail as { asset_id: string }).asset_id)).toEqual(['ka_gochara_v4_41_candidate'])
    info.mockRestore(); error.mockRestore()
  })

  it('derives the freshness deadline in PostgreSQL from a microsecond source timestamp', async () => {
    const sourceTimestamp = '2026-08-28T08:00:00.123456Z'
    successfulSources({ observedAt: sourceTimestamp })
    const { POST } = await import('../route')

    const response = await POST(request({ Authorization: `Bearer ${schedulerOidcToken}` }))

    expect(response.status).toBe(200)
    const [insertSql, insertParams] = insertQueryMock.mock.calls[0] ?? []
    expect(String(insertSql)).toContain("$12::timestamptz + INTERVAL '15 minutes'")
    expect(insertParams).toEqual(expect.arrayContaining([sourceTimestamp]))
  })

  it('keeps stale source freshness, active runtime, and unknown release state distinct', async () => {
    const staleObservedAt = new Date(Date.now() - 16 * 60 * 1000).toISOString()
    successfulSources({ observedAt: staleObservedAt, runs: [{ id: 'run-active' }] })
    releaseMock.mockResolvedValueOnce({
      release: {
        main_sha: 'a'.repeat(40), deployed_sha: null, deployed_revision: 'amjis-web-01705-abc',
        production_in_sync: null, observed_at: sourceObservedAt,
      },
      sources: [
        { source_id: 'github_main', state: 'fresh', observed_at: sourceObservedAt, age_seconds: 0 },
        { source_id: 'cloud_run_web', state: 'fresh', observed_at: sourceObservedAt, age_seconds: 0 },
        { source_id: 'artifact_registry_commit', state: 'unknown', observed_at: sourceObservedAt, age_seconds: null },
      ],
      gaps: ['Immutable release provenance is unavailable.'],
    })
    const { POST } = await import('../route')
    const response = await POST(request({ Authorization: `Bearer ${schedulerOidcToken}` }))
    expect(response.status).toBe(200)
    expect(await response.json()).toMatchObject({
      source_state: 'available', freshness_state: 'stale', runtime_liveness: 'active',
      release_state: 'unknown',
    })
    expect(insertQueryMock.mock.calls[0]?.[1]).toEqual(expect.arrayContaining([
      'available', 'stale', 'active', 'unknown',
    ]))
  })

  it('records safe unavailable/liveness state without passing the caught secret to persistence or logs', async () => {
    const log = vi.spyOn(console, 'error').mockImplementation(() => undefined)
    successfulSources()
    clientQueryMock.mockImplementationOnce(() => Promise.reject(sensitiveDatabaseError('super-secret', 'private-db.internal')))
    const { POST } = await import('../route')
    const response = await POST(request({ Authorization: `Bearer ${schedulerOidcToken}` }))
    const body = await response.json()
    expect(response.status).toBe(200)
    expect(body).toMatchObject({
      status: 'source_unavailable', source_state: 'unavailable', freshness_state: 'unavailable',
      runtime_liveness: 'unavailable', release_state: 'unavailable',
    })
    const observable = JSON.stringify({ body, insert: insertQueryMock.mock.calls, logs: log.mock.calls })
    expect(observable).not.toContain('super-secret')
    expect(observable).not.toContain('private-db.internal')
    expect(log).toHaveBeenCalledWith('[nirmana-elevation] monitor source read failed', {
      error_code: 'NIRMANA_SOURCE_UNAVAILABLE',
    })
  })

  it('derives the selected catalogue digest from label content instead of trusting a stored digest stamp', async () => {
    const { buildNirmanaBaselineCandidate } = await import('@/lib/nirmana-elevation/monitor')
    const candidate = buildNirmanaBaselineCandidate([registryRow()])
    successfulSources({
      definitions: [{ definition_revision: 'ntap-v1', definition_status: 'frozen', manifest: candidate.manifest, manifest_sha256: candidate.manifest_sha256 }],
      receipts: [{ catalogue_revision: 'labels-v1', catalogue_sha256: candidate.catalogue_sha256 }],
      labels: [{
        asset_id: 'bg_reference', sanskrit_name: null, english_name: 'Tampered label content',
        description: 'Authoritative reference values.', legacy_aliases: [],
        source_ref: 'asset_registry:bg_reference', label_digest: candidate.catalogue_sha256,
      }],
    })
    const { POST } = await import('../route')
    const response = await POST(request({ Authorization: `Bearer ${schedulerOidcToken}` }))
    expect(response.status).toBe(200)
    expect((await response.json()).status).toBe('label_refresh_required')
  })

  it('returns a sanitized no-store 503 when the observation insert fails', async () => {
    const log = vi.spyOn(console, 'error').mockImplementation(() => undefined)
    successfulSources()
    insertQueryMock.mockRejectedValueOnce(sensitiveDatabaseError('write-secret', 'writer.internal'))
    const { POST } = await import('../route')
    const response = await POST(request({ Authorization: `Bearer ${schedulerOidcToken}` }))
    const body = await response.json()
    expect(response.status).toBe(503)
    expect(response.headers.get('Cache-Control')).toBe('no-store')
    expect(body).toEqual({ ok: false, error: 'monitor_unavailable' })
    expect(JSON.stringify({ body, logs: log.mock.calls })).not.toContain('write-secret')
    expect(JSON.stringify(log.mock.calls)).not.toContain('writer.internal')
    expect(log).toHaveBeenCalledWith('[nirmana-elevation] monitor observation write failed', {
      error_code: 'NIRMANA_MONITOR_WRITE_FAILED',
    })
  })
})
