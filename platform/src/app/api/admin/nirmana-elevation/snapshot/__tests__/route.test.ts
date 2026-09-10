// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { NextResponse } from 'next/server'
import { NirmanaElevationSnapshotV2Schema } from '@/lib/nirmana-elevation/types'

vi.mock('server-only', () => ({}))

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

const authMock = vi.fn()
vi.mock('@/lib/auth/access-control', () => ({ requireSuperAdmin: () => authMock() }))
const releaseMock = vi.fn()
vi.mock('@/lib/nirmana-elevation/release', () => ({ loadNirmanaReleaseStatus: () => releaseMock() }))

function superAdmin() {
  authMock.mockResolvedValue({
    user: { uid: 'admin-1' },
    profile: { id: 'admin-1', role: 'super_admin', status: 'active' },
  })
}

function sourceRows({
  observationId = '30303030-3030-4030-8030-303030303030',
  candidateDefinitionSha256 = 'b'.repeat(64),
  candidateCatalogueSha256 = 'c'.repeat(64),
  monitorObservedAt = '2026-08-25T08:44:00.000Z',
  monitorStatus = 'plan_adaptation_required',
  monitorSourceState = 'available',
  includeMonitorObservation = true,
}: {
  observationId?: string
  candidateDefinitionSha256?: string
  candidateCatalogueSha256?: string
  monitorObservedAt?: string
  monitorStatus?: 'baseline_missing' | 'plan_adaptation_required' | 'source_unavailable'
  monitorSourceState?: 'available' | 'unavailable'
  includeMonitorObservation?: boolean
} = {}) {
  queryMock
    .mockResolvedValueOnce({ rows: [{ asset_id: 'bg_prashna_rules', english_name: 'Prashna Rules', layer: 'brahmagyan', sort_order: 1, has_writer: true, asset_type: 'data', asset_kind: 'data', is_active: true, depends_on: [] }] })
    .mockResolvedValueOnce({ rows: [{ asset_id: 'bg_prashna_rules', state: 'lit', last_built_at: '2026-08-25T09:00:00.000Z' }] })
    .mockResolvedValueOnce({ rows: [] })
    .mockResolvedValueOnce({ rows: [] })
    .mockResolvedValueOnce({ rows: [] })
    .mockResolvedValueOnce({ rows: [] })
    .mockResolvedValueOnce({ rows: [] })
    .mockResolvedValueOnce({ rows: [] })
    .mockResolvedValueOnce({ rows: includeMonitorObservation ? [{
      id: observationId, observed_at: monitorObservedAt,
      status: monitorStatus, affected_asset_ids: ['bg_prashna_rules'],
      current_definition_sha256: 'a'.repeat(64), candidate_definition_sha256: candidateDefinitionSha256,
      candidate_catalogue_sha256: candidateCatalogueSha256,
      source_state: monitorSourceState,
      source_observed_at: monitorSourceState === 'available' ? monitorObservedAt : null,
      freshness_state: monitorSourceState === 'available' ? 'fresh' : 'unavailable',
      freshness_deadline_at: monitorSourceState === 'available'
        ? new Date(Date.parse(monitorObservedAt) + 15 * 60_000).toISOString() : null,
      source_error_code: null, runtime_liveness: 'quiet',
    }] : [] })
}

describe('GET /api/admin/nirmana-elevation/snapshot', () => {
  afterEach(() => vi.restoreAllMocks())

  beforeEach(() => {
    vi.resetModules()
    queryMock.mockReset()
    authMock.mockReset()
    releaseMock.mockReset().mockResolvedValue({
      release: { main_sha: 'a'.repeat(40), deployed_sha: null, deployed_revision: 'amjis-web-01704-mvb', production_in_sync: null, observed_at: '2026-08-25T09:00:00.000Z' },
      sources: [
        { source_id: 'github_main', provenance: 'GitHub public commits API', state: 'fresh', observed_at: '2026-08-25T09:00:00.000Z', age_seconds: 0, error_code: null, error_message: null },
        { source_id: 'cloud_run_web', provenance: 'Cloud Run Service traffic via ADC', state: 'fresh', observed_at: '2026-08-25T09:00:00.000Z', age_seconds: 0, error_code: null, error_message: null },
        { source_id: 'artifact_registry_commit', provenance: 'Serving revision immutable commit provenance', state: 'unknown', observed_at: '2026-08-25T09:00:00.000Z', age_seconds: null, error_code: 'NIRMANA_RELEASE_PROVENANCE_UNAVAILABLE', error_message: 'Immutable serving-revision commit provenance is unavailable.' },
      ],
      gaps: ['Serving revision commit SHA is not published as immutable Cloud Run provenance; production sync is withheld.'],
    })
  })

  it('protects the snapshot before any evidence query', async () => {
    authMock.mockResolvedValue(NextResponse.json({ error: 'forbidden' }, { status: 403 }))
    const { GET } = await import('../route')

    const response = await GET()

    expect(response.status).toBe(403)
    expect(response.headers.get('Cache-Control')).toBe('no-store')
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('returns a no-store, ETagged, schema-valid reconciliation snapshot for a super-admin', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-08-25T09:00:00.000Z'))
    try {
      const sourceObservationId = '30303030-3030-4030-8030-303030303030'
      superAdmin()
      sourceRows({
        observationId: sourceObservationId,
        monitorObservedAt: '2026-08-25T08:59:00.000Z',
        monitorStatus: 'baseline_missing',
      })
      const { GET } = await import('../route')

      const response = await GET()
      const body = await response.json()
      const snapshot = NirmanaElevationSnapshotV2Schema.parse(body)

      expect(response.status).toBe(200)
      expect(response.headers.get('Cache-Control')).toBe('no-store')
      expect(response.headers.get('ETag')).toMatch(/^"[a-f0-9]{64}"$/)
      expect(snapshot.campaign.campaign_status).toBe('unknown')
      expect(snapshot.schema_version).toBe('2.0')
      expect(snapshot.campaign.current_stage).toBeNull()
      expect(snapshot.stages).toHaveLength(13)
      expect(snapshot.progress.assets_total).toBeNull()
      expect(snapshot.release).toMatchObject({ main_sha: 'a'.repeat(40), deployed_sha: null, deployed_revision: 'amjis-web-01704-mvb', production_in_sync: null })
      expect(snapshot.sources).toEqual(expect.arrayContaining([expect.objectContaining({ source_id: 'github_main', state: 'fresh' })]))
      expect(snapshot.program_sync).toMatchObject({
        status: 'baseline_missing', source_observation_id: sourceObservationId,
        affected_asset_ids: ['bg_prashna_rules'],
        current_definition_sha256: 'a'.repeat(64), candidate_definition_sha256: 'b'.repeat(64),
        candidate_catalogue_sha256: 'c'.repeat(64),
      })
      expect(snapshot.sources).toEqual(expect.arrayContaining([
        expect.objectContaining({ source_id: 'program_monitor', state: 'fresh' }),
      ]))
      // The primary build evidence is fresh, but the denominator and release
      // reconciliation are intentionally not frozen in the takeover baseline.
      expect(snapshot.data_quality.verdict).toBe('degraded')
      const sql = queryMock.mock.calls.map(([statement]) => String(statement)).join('\n')
      expect(sql).toContain('asset_registry')
      expect(sql).toContain('asset_throughput')
      expect(sql).toContain('build_runs')
      expect(sql).toContain('build_run_assets')
      expect(sql).toContain('build_substep_progress')
      expect(sql).toContain('nirmana_elevation_asset_labels')
      expect(sql).toContain('nirmana_elevation_monitor_observations')
      expect(sql).toContain('source_observed_at')
      expect(sql).toContain('freshness_state')
      expect(sql).toContain('freshness_deadline_at')
      expect(sql).toContain('WHERE EXISTS (SELECT 1 FROM build_runs br')
    } finally {
      vi.useRealTimers()
    }
  })

  it('changes the ETag when only the source observation identity changes', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-08-25T09:00:00.000Z'))
    try {
      superAdmin()
      sourceRows({ observationId: '30303030-3030-4030-8030-303030303030' })
      sourceRows({ observationId: '40404040-4040-4040-8040-404040404040' })
      const { GET } = await import('../route')

      const first = await GET()
      const second = await GET()

      expect(first.status).toBe(200)
      expect(second.status).toBe(200)
      expect(first.headers.get('ETag')).toMatch(/^"[a-f0-9]{64}"$/)
      expect(second.headers.get('ETag')).toMatch(/^"[a-f0-9]{64}"$/)
      expect(second.headers.get('ETag')).not.toBe(first.headers.get('ETag'))
    } finally {
      vi.useRealTimers()
    }
  })

  it.each([
    ['no observation', { includeMonitorObservation: false }],
    ['unavailable observation', { monitorStatus: 'source_unavailable' as const, monitorSourceState: 'unavailable' as const }],
  ])('projects a null source observation identity for %s', async (_scenario, options) => {
    superAdmin()
    sourceRows(options)
    const { GET } = await import('../route')

    const response = await GET()
    const body = await response.json()

    expect(response.status).toBe(200)
    expect(body.program_sync.source_observation_id).toBeNull()
  })

  it('returns an explicit degraded 503 snapshot when any authoritative source fails', async () => {
    superAdmin()
    const log = vi.spyOn(console, 'error').mockImplementation(() => undefined)
    queryMock.mockRejectedValueOnce(new Error('password=super-secret host=private-db.internal'))
    const { GET } = await import('../route')

    const response = await GET()
    const body = await response.json()

    expect(response.status).toBe(503)
    expect(response.headers.get('Cache-Control')).toBe('no-store')
    expect(body.schema_version).toBe('2.0')
    expect(body.campaign.current_stage).toBeNull()
    expect(body.stages).toHaveLength(13)
    expect(body.data_quality.verdict).toBe('degraded')
    expect(body.sources).toEqual(expect.arrayContaining([
      expect.objectContaining({
        source_id: 'asset_registry', state: 'unavailable',
        error_code: 'NIRMANA_SOURCE_UNAVAILABLE',
        error_message: 'Authoritative source is unavailable.',
      }),
    ]))
    expect(JSON.stringify(body)).not.toContain('super-secret')
    expect(JSON.stringify(body)).not.toContain('private-db.internal')
    expect(log).toHaveBeenCalledWith(
      '[nirmana-elevation] authoritative source query failed',
      { source_id: 'asset_registry', error_code: 'NIRMANA_SOURCE_UNAVAILABLE' },
    )
    expect(JSON.stringify(log.mock.calls)).not.toContain('super-secret')
    expect(JSON.stringify(log.mock.calls)).not.toContain('private-db.internal')
    expect(body.progress.assets_total).toBeNull()
    expect(body.assets).toEqual([])
    expect(body.program_sync.source_observation_id).toBeNull()
  })

  it('sanitizes a secret-shaped program-monitor query failure in both response and logs', async () => {
    superAdmin()
    const log = vi.spyOn(console, 'error').mockImplementation(() => undefined)
    queryMock
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] })
      .mockRejectedValueOnce(new Error('password=monitor-secret host=monitor-db.internal'))
    const { GET } = await import('../route')

    const response = await GET()
    const body = await response.json()

    expect(response.status).toBe(503)
    expect(body.sources).toEqual(expect.arrayContaining([
      expect.objectContaining({
        source_id: 'program_monitor', state: 'unavailable',
        error_code: 'NIRMANA_SOURCE_UNAVAILABLE',
        error_message: 'Authoritative source is unavailable.',
      }),
    ]))
    expect(body.program_sync.source_observation_id).toBeNull()
    expect(log).toHaveBeenCalledWith(
      '[nirmana-elevation] authoritative source query failed',
      { source_id: 'program_monitor', error_code: 'NIRMANA_SOURCE_UNAVAILABLE' },
    )
    const exposed = `${JSON.stringify(body)}\n${JSON.stringify(log.mock.calls)}`
    expect(exposed).not.toContain('monitor-secret')
    expect(exposed).not.toContain('monitor-db.internal')
  })

  it('returns the label catalogue as an explicit unavailable authoritative source before migration application', async () => {
    superAdmin()
    queryMock
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] })
      .mockRejectedValueOnce(new Error('relation "nirmana_elevation_asset_labels" does not exist'))
    const { GET } = await import('../route')

    const response = await GET()
    const body = await response.json()

    expect(response.status).toBe(503)
    expect(response.headers.get('Cache-Control')).toBe('no-store')
    expect(body.schema_version).toBe('2.0')
    expect(body.sources).toEqual(expect.arrayContaining([
      expect.objectContaining({
        source_id: 'asset_label_catalogue', state: 'unavailable',
        error_code: 'NIRMANA_SOURCE_UNAVAILABLE',
        error_message: 'Authoritative source is unavailable.',
      }),
    ]))
    expect(JSON.stringify(body)).not.toContain('does not exist')
    expect(JSON.stringify(body)).not.toContain('relation "')
  })
})
