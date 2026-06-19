import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))
vi.mock('@/lib/auth/access-control', () => ({
  getServerUserWithProfile: vi.fn(),
}))
vi.mock('@/lib/storage', () => ({
  getStorageClient: vi.fn(() => ({})),
}))
vi.mock('@/lib/admin/trace_assembler', () => ({
  assembleTrace: vi.fn(),
  assembleTraceFull: vi.fn(),
}))

import { NextRequest } from 'next/server'
import { GET } from '@/app/api/admin/trace/[query_id]/route'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { assembleTraceFull } from '@/lib/admin/trace_assembler'

const QUERY_ID = 'dddddddd-0000-0000-0000-000000000001'

function makeReq() {
  return new NextRequest(`http://localhost/api/admin/trace/${QUERY_ID}`)
}

describe('GET /api/admin/trace/[query_id]', () => {
  beforeEach(() => vi.clearAllMocks())

  it('returns 401 when user is not authenticated', async () => {
    vi.mocked(getServerUserWithProfile).mockResolvedValue(null)
    const res = await GET(makeReq(), { params: Promise.resolve({ query_id: QUERY_ID }) })
    expect(res.status).toBe(401)
    const body = await res.json()
    expect(body.error).toBe('Unauthorized')
  })

  it('returns 403 for a client (non-super_admin) user', async () => {
    vi.mocked(getServerUserWithProfile).mockResolvedValue({
      user: { uid: 'user-1' } as never,
      profile: { id: 'user-1', role: 'guest', status: 'active' },
    })
    const res = await GET(makeReq(), { params: Promise.resolve({ query_id: QUERY_ID }) })
    expect(res.status).toBe(403)
    const body = await res.json()
    expect(body.error).toBe('Forbidden')
  })

  it('returns 403 for a super_admin with inactive status', async () => {
    vi.mocked(getServerUserWithProfile).mockResolvedValue({
      user: { uid: 'admin-1' } as never,
      profile: { id: 'admin-1', role: 'super_admin', status: 'disabled' },
    })
    const res = await GET(makeReq(), { params: Promise.resolve({ query_id: QUERY_ID }) })
    expect(res.status).toBe(403)
  })

  it('returns 200 with TraceEnvelope (assembled + legacy + steps) for authenticated super_admin', async () => {
    vi.mocked(getServerUserWithProfile).mockResolvedValue({
      user: { uid: 'admin-1' } as never,
      profile: { id: 'admin-1', role: 'super_admin', status: 'active' },
    })
    const mockEnvelope = {
      assembled: {
        query_id: QUERY_ID,
        query_text: null,
        total_latency_ms: null,
        query_plan: null,
        steps: [],
        grouped: {
          planner: null,
          retrieval: [],
          synthesis: null,
          audit: null,
          checkpoints: [],
        },
        partial: true,
      },
      legacy: { query: { id: QUERY_ID, health: 'UNKNOWN' }, partial: true },
      steps: [],
    }
    vi.mocked(assembleTraceFull).mockResolvedValue(mockEnvelope as never)

    const res = await GET(makeReq(), { params: Promise.resolve({ query_id: QUERY_ID }) })
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.assembled.query_id).toBe(QUERY_ID)
    expect(body.legacy.query.id).toBe(QUERY_ID)
    expect(Array.isArray(body.steps)).toBe(true)
    expect(assembleTraceFull).toHaveBeenCalledWith(QUERY_ID, expect.anything())
  })
})
