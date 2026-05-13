import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

const { mockGenerateText, mockResolveModel, mockGetEffectiveModel } = vi.hoisted(() => ({
  mockGenerateText:     vi.fn(),
  mockResolveModel:     vi.fn(),
  mockGetEffectiveModel: vi.fn(),
}))

vi.mock('ai', () => ({ generateText: mockGenerateText }))
vi.mock('@/lib/models/resolver', () => ({ resolveModel: mockResolveModel }))
vi.mock('@/lib/models/runtime_config', () => ({ getEffectiveModel: mockGetEffectiveModel }))
vi.mock('@/lib/models/registry', async () => {
  const actual = await vi.importActual<typeof import('@/lib/models/registry')>('@/lib/models/registry')
  return {
    ...actual,
    DEFAULT_STACK_ID: 'gemini',
    STACK_ROUTING: {
      gemini: {
        synthesis: { primary: 'gemini-2.5-pro', fallback: 'gemini-2.0-flash' },
      },
    },
    getModelMeta: vi.fn().mockReturnValue({ costPer1MInput: 1.25, costPer1MOutput: 5.0 }),
  }
})

const MOCK_MODEL = { _type: 'mock-model' }

describe('runProbe', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockResolveModel.mockReturnValue(MOCK_MODEL)
    mockGetEffectiveModel.mockResolvedValue('gemini-2.5-pro')
  })

  it('returns pass status on successful model call', async () => {
    mockGenerateText.mockResolvedValueOnce({
      text: 'Mars in the 7th house indicates partnerships.',
      finishReason: 'stop',
      usage: { inputTokens: 50, outputTokens: 20 },
    })
    const { runProbe } = await import('../runner')
    const result = await runProbe({ stack: 'gemini', callType: 'synthesis', role: 'primary' })
    expect(result.status).toBe('pass')
    expect(result.model_id).toBe('gemini-2.5-pro')
    expect(result.input_tokens).toBe(50)
    expect(result.output_tokens).toBe(20)
    expect(result.output_text.length).toBeLessThanOrEqual(300)
  })

  it('truncates output_text to 300 chars', async () => {
    const longText = 'a'.repeat(400)
    mockGenerateText.mockResolvedValueOnce({ text: longText, finishReason: 'length', usage: {} })
    const { runProbe } = await import('../runner')
    const result = await runProbe({ stack: 'gemini', callType: 'synthesis', role: 'primary' })
    expect(result.output_text.length).toBe(300)
  })

  it('returns fail on unknown model_override', async () => {
    mockResolveModel.mockImplementationOnce(() => { throw new Error('Unknown model id: bad-model') })
    const { runProbe } = await import('../runner')
    const result = await runProbe({ stack: 'gemini', callType: 'synthesis', role: 'primary', modelOverride: 'bad-model' })
    expect(result.status).toBe('fail')
    expect(result.error).toMatch(/Unknown model/)
  })

  it('returns timeout on AbortError', async () => {
    const abortErr = Object.assign(new Error('Aborted'), { name: 'AbortError' })
    mockGenerateText.mockRejectedValueOnce(abortErr)
    const { runProbe } = await import('../runner')
    const result = await runProbe({ stack: 'gemini', callType: 'synthesis', role: 'primary' })
    expect(result.status).toBe('timeout')
  })

  it('returns fail on network error', async () => {
    mockGenerateText.mockRejectedValueOnce(new Error('network fail'))
    const { runProbe } = await import('../runner')
    const result = await runProbe({ stack: 'gemini', callType: 'synthesis', role: 'primary' })
    expect(result.status).toBe('fail')
    expect(result.error).toBeTruthy()
  })

  it('uses modelOverride when provided', async () => {
    mockGenerateText.mockResolvedValueOnce({ text: 'ok', finishReason: 'stop', usage: {} })
    const { runProbe } = await import('../runner')
    const result = await runProbe({ stack: 'gemini', callType: 'synthesis', role: 'primary', modelOverride: 'gemini-custom' })
    expect(result.model_id).toBe('gemini-custom')
  })

  it('computes cost_usd from model metadata', async () => {
    mockGenerateText.mockResolvedValueOnce({ text: 'ok', finishReason: 'stop', usage: { inputTokens: 1000, outputTokens: 200 } })
    const { runProbe } = await import('../runner')
    const result = await runProbe({ stack: 'gemini', callType: 'synthesis', role: 'primary' })
    // 1000 * 1.25/1M + 200 * 5.0/1M = 0.00125 + 0.001 = 0.00225
    expect(result.cost_usd).toBeCloseTo(0.00225, 5)
  })

  it('returns correct call_type and role in result', async () => {
    mockGenerateText.mockResolvedValueOnce({ text: 'plan', finishReason: 'stop', usage: {} })
    const { runProbe } = await import('../runner')
    const result = await runProbe({ stack: 'gemini', callType: 'planner_fast', role: 'fallback' })
    expect(result.call_type).toBe('planner_fast')
    expect(result.role).toBe('fallback')
  })

  it('returns latency_ms > 0', async () => {
    mockGenerateText.mockResolvedValueOnce({ text: 'ok', finishReason: 'stop', usage: {} })
    const { runProbe } = await import('../runner')
    const result = await runProbe({ stack: 'gemini', callType: 'worker', role: 'primary' })
    expect(result.latency_ms).toBeGreaterThanOrEqual(0)
  })
})
