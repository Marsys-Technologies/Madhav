import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

const { mockRunProbe, mockQuery } = vi.hoisted(() => ({
  mockRunProbe: vi.fn(),
  mockQuery:    vi.fn(),
}))

vi.mock('@/lib/aiops/probe/runner', () => ({ runProbe: mockRunProbe }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { probeModel } from '../prober'

describe('probeModel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockQuery.mockResolvedValue({ rows: [] })
  })

  it('returns pass result and upserts health row on success', async () => {
    mockRunProbe.mockResolvedValue({ status: 'pass', latency_ms: 123, error: undefined })
    const result = await probeModel('gemini-2.5-pro')
    expect(result.model_id).toBe('gemini-2.5-pro')
    expect(result.status).toBe('pass')
    expect(result.latency_ms).toBe(123)
    expect(mockQuery).toHaveBeenCalledOnce()
    const [sql, params] = mockQuery.mock.calls[0] as [string, unknown[]]
    expect(sql).toContain('INSERT INTO llm_model_health')
    expect(params[0]).toBe('gemini-2.5-pro')
    expect(params[1]).toBe('pass')
    expect(params[2]).toBe(123)
  })

  it('returns fail status when probe returns fail', async () => {
    mockRunProbe.mockResolvedValue({ status: 'fail', latency_ms: null, error: 'timeout' })
    const result = await probeModel('some-model')
    expect(result.status).toBe('fail')
    expect(result.latency_ms).toBeNull()
  })

  it('returns timeout status when probe returns timeout', async () => {
    mockRunProbe.mockResolvedValue({ status: 'timeout', latency_ms: null, error: 'timed out' })
    const result = await probeModel('some-model')
    expect(result.status).toBe('timeout')
  })

  it('catches runProbe exception and records fail with error message', async () => {
    mockRunProbe.mockRejectedValue(new Error('network error'))
    const result = await probeModel('bad-model')
    expect(result.status).toBe('fail')
    expect(result.error).toBe('network error')
    expect(result.latency_ms).toBeNull()
    expect(mockQuery).toHaveBeenCalledOnce()
    const [, params] = mockQuery.mock.calls[0] as [string, unknown[]]
    expect(params[1]).toBe('fail')
  })

  it('upserts null for error field when probe passes cleanly', async () => {
    mockRunProbe.mockResolvedValue({ status: 'pass', latency_ms: 50 })
    await probeModel('clean-model')
    const [, params] = mockQuery.mock.calls[0] as [string, unknown[]]
    expect(params[3]).toBeNull() // last_error
  })

  it('calls runProbe with correct shape (gemini stack, worker call type)', async () => {
    mockRunProbe.mockResolvedValue({ status: 'pass', latency_ms: 10 })
    await probeModel('test-model-x')
    expect(mockRunProbe).toHaveBeenCalledWith({
      stack:         'gemini',
      callType:      'worker',
      role:          'primary',
      modelOverride: 'test-model-x',
    })
  })
})
