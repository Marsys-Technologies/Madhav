// @vitest-environment node
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { NextResponse } from 'next/server'

vi.mock('server-only', () => ({}))

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

const authMock = vi.fn()
vi.mock('@/lib/auth/access-control', () => ({ requireSuperAdmin: () => authMock() }))

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
}

describe('GET /api/admin/nirmana-elevation/snapshot', () => {
  beforeEach(() => {
    vi.resetModules()
    queryMock.mockReset()
    authMock.mockReset()
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
    expect(body.campaign.campaign_status).toBe('takeover')
    expect(body.progress.assets_total).toBeNull()
    // The primary build evidence is fresh, but the denominator and release
    // reconciliation are intentionally not frozen in the takeover baseline.
    expect(body.data_quality.verdict).toBe('degraded')
    const sql = queryMock.mock.calls.map(([statement]) => String(statement)).join('\n')
    expect(sql).toContain('asset_registry')
    expect(sql).toContain('asset_throughput')
    expect(sql).toContain('build_runs')
    expect(sql).toContain('build_run_assets')
    expect(sql).toContain('build_substep_progress')
    expect(sql).toContain('WHERE EXISTS (SELECT 1 FROM build_runs br')
  })

  it('returns an explicit degraded 503 snapshot when any authoritative source fails', async () => {
    superAdmin()
    queryMock.mockRejectedValueOnce(new Error('database unavailable'))
    const { GET } = await import('../route')

    const response = await GET()
    const body = await response.json()

    expect(response.status).toBe(503)
    expect(response.headers.get('Cache-Control')).toBe('no-store')
    expect(body.data_quality.verdict).toBe('degraded')
    expect(body.sources).toEqual(expect.arrayContaining([
      expect.objectContaining({ source_id: 'asset_registry', state: 'unavailable', error: 'database unavailable' }),
    ]))
    expect(body.progress.assets_total).toBeNull()
    expect(body.assets).toEqual([])
  })
})
