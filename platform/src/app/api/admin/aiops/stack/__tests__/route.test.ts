import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextResponse } from 'next/server'

vi.mock('server-only', () => ({}))

const { mockRequireSuperAdmin, mockQuery, mockInvalidate } = vi.hoisted(() => ({
  mockRequireSuperAdmin: vi.fn(),
  mockQuery:             vi.fn(),
  mockInvalidate:        vi.fn(),
}))

vi.mock('@/lib/auth/access-control', () => ({ requireSuperAdmin: mockRequireSuperAdmin }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/models/runtime_config', () => ({ invalidateRuntimeConfigCache: mockInvalidate }))

const MOCK_AUTH = { user: { uid: 'admin1' }, profile: { role: 'super_admin', status: 'active' } }

function makeRequest(body: unknown): Request {
  return new Request('http://localhost', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

describe('PUT /api/admin/aiops/stack', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubEnv('MARSYS_FLAG_OBSERVATORY_ENABLED', 'true')
    mockRequireSuperAdmin.mockResolvedValue(MOCK_AUTH)
    mockQuery.mockResolvedValue({ rows: [] })
  })

  it('returns 403 when flag is off', async () => {
    vi.stubEnv('MARSYS_FLAG_OBSERVATORY_ENABLED', 'false')
    const { PUT } = await import('../route')
    const res = await PUT(makeRequest({ active_stack: 'nim' }))
    expect(res.status).toBe(403)
  })

  it('returns 401 when unauthenticated', async () => {
    mockRequireSuperAdmin.mockResolvedValue(
      NextResponse.json({ error: {} }, { status: 401 }),
    )
    const { PUT } = await import('../route')
    const res = await PUT(makeRequest({ active_stack: 'nim' }))
    expect(res.status).toBe(401)
  })

  it('returns 400 for unknown stack', async () => {
    const { PUT } = await import('../route')
    const res = await PUT(makeRequest({ active_stack: 'unknown' }))
    expect(res.status).toBe(400)
  })

  it('returns 200 with new active_stack on valid input', async () => {
    const { PUT } = await import('../route')
    const res = await PUT(makeRequest({ active_stack: 'nim' }))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.active_stack).toBe('nim')
  })

  it('calls invalidateRuntimeConfigCache after update', async () => {
    const { PUT } = await import('../route')
    await PUT(makeRequest({ active_stack: 'deepseek' }))
    expect(mockInvalidate).toHaveBeenCalled()
  })

  it('writes audit row alongside config update', async () => {
    const { PUT } = await import('../route')
    await PUT(makeRequest({ active_stack: 'gpt' }))
    const insertCalls = mockQuery.mock.calls.filter(c => (c[0] as string).includes('llm_config_audit'))
    expect(insertCalls).toHaveLength(1)
  })
})
