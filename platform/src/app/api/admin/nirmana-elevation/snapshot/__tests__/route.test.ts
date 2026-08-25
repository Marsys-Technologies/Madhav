// @vitest-environment node
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { NextResponse } from 'next/server'

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

function sourceRows() {
  queryMock
    .mockResolvedValueOnce({ rows: [{ asset_id: 'bg_prashna_rules', english_name: 'Prashna Rules', layer: 'brahmagyan', sort_order: 1, has_writer: true, asset_type: 'data', asset_kind: 'data', is_active: true, depends_on: [] }] })
    .mockResolvedValueOnce({ rows: [{ asset_id: 'bg_prashna_rules', state: 'lit', last_built_at: '2026-08-25T09:00:00.000Z' }] })
    .mockResolvedValueOnce({ rows: [] })
    .mockResolvedValueOnce({ rows: [] })
    .mockResolvedValueOnce({ rows: [] })
    .mockResolvedValueOnce({ rows: [] })
    .mockResolvedValueOnce({ rows: [] })
    .mockResolvedValueOnce({ rows: [] })
}

describe('GET /api/admin/nirmana-elevation/snapshot', () => {
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
    superAdmin()
    sourceRows()
    const { GET } = await import('../route')

    const response = await GET()
    const body = await response.json()

    expect(response.status).toBe(200)
    expect(response.headers.get('Cache-Control')).toBe('no-store')
    expect(response.headers.get('ETag')).toMatch(/^"[a-f0-9]{64}"$/)
    expect(body.campaign.campaign_status).toBe('unknown')
    expect(body.schema_version).toBe('2.0')
    expect(body.campaign.current_stage).toBeNull()
    expect(body.stages).toHaveLength(13)
    expect(body.progress.assets_total).toBeNull()
    expect(body.release).toMatchObject({ main_sha: 'a'.repeat(40), deployed_sha: null, deployed_revision: 'amjis-web-01704-mvb', production_in_sync: null })
    expect(body.sources).toEqual(expect.arrayContaining([expect.objectContaining({ source_id: 'github_main', state: 'fresh' })]))
    // The primary build evidence is fresh, but the denominator and release
    // reconciliation are intentionally not frozen in the takeover baseline.
    expect(body.data_quality.verdict).toBe('degraded')
    const sql = queryMock.mock.calls.map(([statement]) => String(statement)).join('\n')
    expect(sql).toContain('asset_registry')
    expect(sql).toContain('asset_throughput')
    expect(sql).toContain('build_runs')
    expect(sql).toContain('build_run_assets')
    expect(sql).toContain('build_substep_progress')
    expect(sql).toContain('nirmana_elevation_asset_labels')
    expect(sql).toContain('WHERE EXISTS (SELECT 1 FROM build_runs br')
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
      expect.objectContaining({ source_id: 'asset_registry', cause: expect.any(Error) }),
    )
    expect(body.progress.assets_total).toBeNull()
    expect(body.assets).toEqual([])
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
