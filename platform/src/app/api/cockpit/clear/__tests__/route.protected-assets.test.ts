/**
 * SHAD-DARSHANA sweep-protection Phase 1a, Layer 1/2 — build_protected_assets
 * clear-preview guard, at the route level (POST /api/cockpit/clear).
 *
 * Covers both directions per the task spec: a protected pair is withheld from
 * the clear preview and surfaced explicitly (never silently counted/marked
 * clearable), and a non-protected pair in the same scope proceeds normally.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

const mockGetServerUser = vi.fn()
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

const USER = { uid: 'user-123' }

const REGISTRY_SWEEP = [
  {
    asset_id: 'ka_gochara_sweep', layer: 'kala', depends_on: [], estimated_seconds: 1800,
    scope: 'per_chart', target_table: 'kala_gochara_windows',
    count_sql: 'SELECT count(*) FROM kala_gochara_windows WHERE chart_id=$1',
    english_name: 'Forward Sweep', sanskrit_name: 'Gochara Cakra',
  },
  {
    asset_id: 'ka_kshetra', layer: 'kala', depends_on: [], estimated_seconds: 60,
    scope: 'per_chart', target_table: 'kala_kshetra',
    count_sql: 'SELECT count(*) FROM kala_kshetra WHERE chart_id=$1',
    english_name: 'Kshetra', sanskrit_name: 'Kshetra',
  },
]

function makeReq(body: object): NextRequest {
  return new NextRequest('http://localhost/api/cockpit/clear', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

function seedRole(role: string) {
  mockGetServerUser.mockResolvedValue(USER)
  mockQuery.mockResolvedValueOnce({ rows: [{ role }], rowCount: 1 }) // getUserRole
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('POST /api/cockpit/clear — SHAD-DARSHANA sweep-protection guard', () => {
  it('a protected pair is withheld from the preview and surfaced — never counted or marked clearable', async () => {
    seedRole('client')
    mockQuery
      // Promise.all([registry, build_protected_assets])
      .mockResolvedValueOnce({ rows: REGISTRY_SWEEP, rowCount: REGISTRY_SWEEP.length }) // asset_registry
      .mockResolvedValueOnce({ rows: [{ asset_id: 'ka_gochara_sweep' }], rowCount: 1 }) // build_protected_assets — protected!
      // Only ka_kshetra remains in scope after withholding — its count_sql query.
      .mockResolvedValueOnce({ rows: [{ count: '42' }], rowCount: 1 })

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'layer', scope_target: 'kala' }))
    expect(res.status).toBe(200)
    const body = await res.json()

    // The protected asset never appears as affected/clearable/reset_only.
    expect(body.preview.affected_assets).not.toContain('ka_gochara_sweep')
    expect(body.preview.assets_clearable.some((a: { id: string }) => a.id === 'ka_gochara_sweep')).toBe(false)
    expect(body.preview.assets_reset_only.some((a: { id: string }) => a.id === 'ka_gochara_sweep')).toBe(false)
    expect(body.preview.not_clearable_assets.some((a: { id: string }) => a.id === 'ka_gochara_sweep')).toBe(false)

    // ...and IS surfaced explicitly, with the exact message the task specifies.
    expect(body.preview.protected_assets).toEqual([
      { id: 'ka_gochara_sweep', label: 'Forward Sweep', message: 'protected — native override required' },
    ])

    // The non-protected sibling in the same scope proceeds normally.
    expect(body.preview.affected_assets).toEqual(['ka_kshetra'])
    expect(body.preview.assets_clearable).toEqual([{ id: 'ka_kshetra', label: 'Kshetra', rows: 42 }])
  })

  it('a non-protected pair proceeds normally — protected_assets is empty, never omitted', async () => {
    seedRole('client')
    mockQuery
      .mockResolvedValueOnce({ rows: REGISTRY_SWEEP, rowCount: REGISTRY_SWEEP.length }) // asset_registry
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })                                 // build_protected_assets — none
      .mockResolvedValueOnce({ rows: [{ count: '7' }], rowCount: 1 })                   // ka_gochara_sweep count
      .mockResolvedValueOnce({ rows: [{ count: '42' }], rowCount: 1 })                  // ka_kshetra count

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'layer', scope_target: 'kala' }))
    expect(res.status).toBe(200)
    const body = await res.json()

    expect(body.preview.affected_assets).toEqual(expect.arrayContaining(['ka_gochara_sweep', 'ka_kshetra']))
    expect(body.preview.protected_assets).toEqual([])
  })
})
