import { describe, it, expect, vi, beforeEach } from 'vitest'

// ── Mocks ─────────────────────────────────────────────────────────────────────

vi.mock('@/lib/firebase/server', () => ({
  getServerUser: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({
  query: vi.fn(),
}))

import { GET } from '../route'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

const mockGetServerUser = vi.mocked(getServerUser)
const mockQuery = vi.mocked(query)

// Three-node chain: A1 ← A2 ← A3 (A2 depends on A1, A3 depends on A2)
const THREE_NODE_ROWS = [
  { asset_id: 'A1', depends_on: [],     english_name: 'Alpha', sort_order: 1, layer: 'L1' },
  { asset_id: 'A2', depends_on: ['A1'], english_name: 'Beta',  sort_order: 2, layer: 'L1' },
  { asset_id: 'A3', depends_on: ['A2'], english_name: 'Gamma', sort_order: 3, layer: 'L1' },
]

function makeRequest(params: Record<string, string>) {
  const url = new URL('http://localhost/api/build/cascade')
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v)
  return new Request(url.toString())
}

beforeEach(() => {
  vi.clearAllMocks()
  mockGetServerUser.mockResolvedValue({ uid: 'user-1', email: 'a@b.com' } as never)
  mockQuery.mockResolvedValue({ rows: THREE_NODE_ROWS } as never)
})

// ── Test 1: 401 without auth ──────────────────────────────────────────────────
describe('GET /api/build/cascade', () => {
  it('returns 401 when unauthenticated', async () => {
    mockGetServerUser.mockResolvedValue(null)
    const res = await GET(makeRequest({ asset_id: 'A1' }))
    expect(res.status).toBe(401)
  })

  // ── Test 2: 400 without asset_id ─────────────────────────────────────────
  it('returns 400 when asset_id is missing', async () => {
    const res = await GET(makeRequest({ chart_id: 'chart-123' }))
    expect(res.status).toBe(400)
    const body = await res.json()
    expect(body.error).toContain('asset_id')
  })

  // ── Test 3: empty downstream when asset_registry returns no rows ──────────
  it('returns empty downstream when asset_registry has no rows', async () => {
    mockQuery.mockResolvedValue({ rows: [] } as never)
    const res = await GET(makeRequest({ asset_id: 'A1', chart_id: 'chart-123' }))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.downstream).toEqual([])
    expect(body.total_affected).toBe(0)
  })

  // ── Test 4: correct downstream list by walking depends_on ─────────────────
  // Chain: A1 ← A2 ← A3. Rebuilding A1 → downstream = [A2, A3]
  it('returns A2 and A3 as downstream when rebuilding A1', async () => {
    const res = await GET(makeRequest({ asset_id: 'A1', chart_id: 'chart-123' }))
    expect(res.status).toBe(200)
    const body = await res.json()
    const ids = body.downstream.map((d: { asset_id: string }) => d.asset_id)
    expect(ids).toContain('A2')
    expect(ids).toContain('A3')
    expect(ids).not.toContain('A1') // rebuilt asset excluded
    expect(body.total_affected).toBe(2)
  })

  // ── Test 5: rebuilt asset_id excluded from downstream ─────────────────────
  it('never includes the rebuilt asset_id in downstream', async () => {
    const res = await GET(makeRequest({ asset_id: 'A2', chart_id: 'chart-123' }))
    const body = await res.json()
    const ids = body.downstream.map((d: { asset_id: string }) => d.asset_id)
    expect(ids).not.toContain('A2')
    expect(ids).toContain('A3')
    expect(ids).not.toContain('A1') // A1 is upstream, not downstream
    expect(body.total_affected).toBe(1)
  })
})
