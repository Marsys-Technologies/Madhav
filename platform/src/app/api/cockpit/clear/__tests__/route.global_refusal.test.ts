/**
 * FIX2 (portal Rebuild): the cockpit Clear routes (preview + execute) must never offer or run a
 * clear of a GLOBAL asset from a chart page. A global table is shared by every chart and its
 * DELETE has no chart filter; this holds for super_admin too.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

const { mockQuery, mockGetPool, mockGetServerUser } = vi.hoisted(() => ({
  mockQuery: vi.fn(), mockGetPool: vi.fn(), mockGetServerUser: vi.fn(),
}))
vi.mock('@/lib/db/client', () => ({ query: mockQuery, getPool: mockGetPool }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

import { POST as PREVIEW } from '../route'
import { POST as EXECUTE } from '../execute/route'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const REGISTRY = [
  { asset_id: 'mi_abhilekha', layer: 'mimamsa', depends_on: [], estimated_seconds: 1, scope: 'per_chart',
    target_table: 'mimamsa_journal', is_active: true, count_sql: null, english_name: 'A', sanskrit_name: 'A' },
  { asset_id: 'mi_kula', layer: 'mimamsa', depends_on: [], estimated_seconds: 1, scope: 'global',
    target_table: 'mimamsa_signal_families', is_active: true, count_sql: null, english_name: 'K', sanskrit_name: 'K' },
]
let deletes: string[] = []

function req(path: string, body: object) {
  return new NextRequest(`http://localhost${path}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  deletes = []
  mockGetServerUser.mockResolvedValue({ uid: 'admin' })
  mockQuery.mockImplementation((sql: string) => {
    if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role: 'super_admin' }], rowCount: 1 })
    if (/FROM chart_grants/.test(sql)) return Promise.resolve({ rows: [], rowCount: 0 })
    if (/subject_name/.test(sql)) return Promise.resolve({ rows: [{ subject_name: 'N', name: 'N' }], rowCount: 1 })
    if (/owner_id[\s\S]*FROM charts/.test(sql)) return Promise.resolve({ rows: [{ owner_id: 'someone' }], rowCount: 1 })
    if (/FROM asset_registry/.test(sql)) return Promise.resolve({ rows: REGISTRY, rowCount: REGISTRY.length })
    return Promise.resolve({ rows: [], rowCount: 0 })
  })
  mockGetPool.mockResolvedValue({
    connect: vi.fn().mockResolvedValue({
      query: vi.fn((sql: string) => { if (/^\s*DELETE/i.test(sql)) deletes.push(sql); return Promise.resolve({ rows: [], rowCount: 0 }) }),
      release: vi.fn(),
    }),
  })
})

describe('Clear routes refuse a global asset from a chart page', () => {
  it('preview: an explicit global asset is refused (422, plain words) even for super_admin', async () => {
    const res = await PREVIEW(req('/api/cockpit/clear', { chart_id: CHART, scope: 'asset', scope_target: 'mi_kula' }))
    expect(res.status).toBe(422)
    const body = await res.json()
    expect(body.code).toBe('GLOBAL_CLEAR_FORBIDDEN')
    expect(body.error).toMatch(/shared by every chart/i)
  })

  it('execute: an explicit global asset is refused before the hash check, and no DELETE is issued', async () => {
    const res = await EXECUTE(req('/api/cockpit/clear/execute', {
      chart_id: CHART, scope: 'asset', scope_target: 'mi_kula', preview_hash: 'irrelevant',
    }))
    expect(res.status).toBe(422)
    expect((await res.json()).code).toBe('GLOBAL_CLEAR_FORBIDDEN')
    expect(deletes).toHaveLength(0)
  })

  it('preview: a mixed layer sweep lists only the per-chart asset', async () => {
    const res = await PREVIEW(req('/api/cockpit/clear', { chart_id: CHART, scope: 'layer', scope_target: 'mimamsa' }))
    expect(res.status).toBe(200)
    const text = JSON.stringify(await res.json())
    expect(text).toContain('mi_abhilekha')
    expect(text).not.toContain('mi_kula')
  })
})
