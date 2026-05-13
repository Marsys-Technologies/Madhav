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

function makeParams(id: string) {
  return { params: Promise.resolve({ id }) }
}

function makeRequest() {
  return new Request('http://localhost', { method: 'POST' })
}

function makeAuditRow(overrides: Record<string, unknown>) {
  return {
    id: 1, occurred_at: '', actor_user_id: 'user1', action: 'set_stack', scope: 'global',
    stack: null, call_type: null, param_name: null, before_value: null, after_value: null, notes: null,
    ...overrides,
  }
}

describe('POST /api/admin/aiops/audit/[id]/revert', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.resetModules()
    vi.stubEnv('MARSYS_FLAG_OBSERVATORY_ENABLED', 'true')
    mockRequireSuperAdmin.mockResolvedValue(MOCK_AUTH)
  })

  it('returns 400 for non-numeric id', async () => {
    const { POST } = await import('../route')
    const res = await POST(makeRequest(), makeParams('abc'))
    expect(res.status).toBe(400)
  })

  it('returns 403 when flag is off', async () => {
    vi.stubEnv('MARSYS_FLAG_OBSERVATORY_ENABLED', 'false')
    const { POST } = await import('../route')
    const res = await POST(makeRequest(), makeParams('1'))
    expect(res.status).toBe(403)
  })

  it('returns 404 when audit row not found', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] }) // SELECT
    const { POST } = await import('../route')
    const res = await POST(makeRequest(), makeParams('999'))
    expect(res.status).toBe(404)
  })

  it('reverts set_stack by restoring before_value.active_stack', async () => {
    const row = makeAuditRow({
      action: 'set_stack',
      before_value: { active_stack: 'nim' },
    })
    mockQuery
      .mockResolvedValueOnce({ rows: [row] }) // SELECT audit row
      .mockResolvedValueOnce({ rows: [] })    // INSERT llm_stack_config (revert)
      .mockResolvedValueOnce({ rows: [] })    // INSERT audit log for revert
    const { POST } = await import('../route')
    const res = await POST(makeRequest(), makeParams('1'))
    expect(res.status).toBe(200)
    expect(mockInvalidate).toHaveBeenCalledOnce()
    // Verify revert upserts the before_value stack
    const secondCall = mockQuery.mock.calls[1] as [string, unknown[]]
    expect(secondCall[1][0]).toBe('nim')
  })

  it('reverts set_routing by restoring before_value primary/fallback', async () => {
    const row = makeAuditRow({
      action: 'set_routing',
      stack: 'gemini',
      call_type: 'synthesis',
      before_value: { primary: 'gemini-2.5-pro', fallback: 'gemini-2.0-flash' },
    })
    mockQuery
      .mockResolvedValueOnce({ rows: [row] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] })
    const { POST } = await import('../route')
    const res = await POST(makeRequest(), makeParams('1'))
    expect(res.status).toBe(200)
    expect(mockInvalidate).toHaveBeenCalledOnce()
    const secondCall = mockQuery.mock.calls[1] as [string, unknown[]]
    expect(secondCall[1][2]).toBe('gemini-2.5-pro') // primary_model
  })

  it('reverts reset_routing by deleting the override when no before primary', async () => {
    const row = makeAuditRow({
      action: 'reset_routing',
      stack: 'nim',
      call_type: 'worker',
      before_value: null,
    })
    mockQuery
      .mockResolvedValueOnce({ rows: [row] })
      .mockResolvedValueOnce({ rows: [] }) // DELETE
      .mockResolvedValueOnce({ rows: [] }) // audit log
    const { POST } = await import('../route')
    const res = await POST(makeRequest(), makeParams('1'))
    expect(res.status).toBe(200)
    const secondCall = mockQuery.mock.calls[1] as [string, unknown[]]
    expect(secondCall[0]).toContain('DELETE')
  })

  it('reverts set_param by restoring before_value.param_value', async () => {
    const row = makeAuditRow({
      action: 'set_param',
      stack: 'gemini',
      call_type: 'synthesis',
      param_name: 'temperature',
      before_value: { param_value: 0.3 },
    })
    mockQuery
      .mockResolvedValueOnce({ rows: [row] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] })
    const { POST } = await import('../route')
    const res = await POST(makeRequest(), makeParams('1'))
    expect(res.status).toBe(200)
    expect(mockInvalidate).toHaveBeenCalledOnce()
    const secondCall = mockQuery.mock.calls[1] as [string, unknown[]]
    expect(secondCall[1][3]).toBe(JSON.stringify(0.3))
  })

  it('reverts reset_param by deleting override when param_value was null', async () => {
    const row = makeAuditRow({
      action: 'reset_param',
      stack: 'deepseek',
      call_type: 'planner_fast',
      param_name: 'max_tokens',
      before_value: { param_value: null },
    })
    mockQuery
      .mockResolvedValueOnce({ rows: [row] })
      .mockResolvedValueOnce({ rows: [] }) // DELETE
      .mockResolvedValueOnce({ rows: [] })
    const { POST } = await import('../route')
    const res = await POST(makeRequest(), makeParams('1'))
    expect(res.status).toBe(200)
    const secondCall = mockQuery.mock.calls[1] as [string, unknown[]]
    expect(secondCall[0]).toContain('DELETE')
  })

  it('writes a revert audit row after successful revert', async () => {
    const row = makeAuditRow({
      action: 'set_stack',
      before_value: { active_stack: 'gemini' },
    })
    mockQuery
      .mockResolvedValueOnce({ rows: [row] })
      .mockResolvedValueOnce({ rows: [] }) // revert action
      .mockResolvedValueOnce({ rows: [] }) // audit insert
    const { POST } = await import('../route')
    await POST(makeRequest(), makeParams('1'))
    const lastCall = mockQuery.mock.calls[2] as [string, unknown[]]
    expect(lastCall[0]).toContain("action, scope, stack")
    expect(lastCall[1][4]).toContain('reverted audit id')
  })

  it('returns 200 JSON with reverted id on success', async () => {
    const row = makeAuditRow({
      action: 'set_stack',
      before_value: { active_stack: 'gpt' },
    })
    mockQuery
      .mockResolvedValueOnce({ rows: [row] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] })
    const { POST } = await import('../route')
    const res = await POST(makeRequest(), makeParams('1'))
    const body = await res.json() as { reverted: number }
    expect(body.reverted).toBe(1)
  })
})
