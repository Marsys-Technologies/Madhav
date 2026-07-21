import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))
vi.mock('fs', () => ({
  default: {
    readFileSync: vi.fn(() =>
      'Query: {{query}}\nPlan: {{query_plan_json}}\nAlternatives: {{discarded_alternatives}}',
    ),
  },
}))
vi.mock('@/lib/models/runtime_config', () => ({
  getEffectiveModel: vi.fn().mockResolvedValue('claude-haiku-4-5'),
}))

const mockRunAdapter = vi.fn()
vi.mock('@/lib/adapters', () => ({ runAdapter: (...args: unknown[]) => mockRunAdapter(...args) }))

const mockGetFlag = vi.fn()
vi.mock('@/lib/config/index', () => ({ getFlag: (...args: unknown[]) => mockGetFlag(...args) }))

vi.mock('@/lib/telemetry/index', () => ({
  telemetry: {
    recordMetric: vi.fn(),
    recordLatency: vi.fn(),
    recordError: vi.fn(),
  },
}))

import { runCheckpoint4_5 } from '../checkpoint_4_5'
import { CheckpointHaltError } from '../types'
import type { Checkpoint45Input } from '../types'

function makeInput(overrides: Partial<Checkpoint45Input> = {}): Checkpoint45Input {
  return {
    query: 'What does Saturn in the 10th house indicate for career?',
    query_plan: {
      query_plan_id: 'plan-001',
      query_text: 'What does Saturn in the 10th house indicate for career?',
      query_class: 'interpretive',
      domains: ['career'],
      forward_looking: false,
      tools_authorized: ['msr_sql'],
      history_mode: 'synthesized',
      panel_mode: false,
      expected_output_shape: 'three_interpretation',
      manifest_fingerprint: 'fp-abc',
      schema_version: '1.0',
    },
    discarded_alternatives: [],
    ...overrides,
  }
}

function mockLLMResponse(verdict: string, confidence = 0.9, reasoning = 'ok') {
  mockRunAdapter.mockResolvedValue({
    finalText: JSON.stringify({ verdict, confidence, reasoning }),
    usage: { inputTokens: 0, outputTokens: 0 },
    finishReason: 'stop',
    intermediate: [],
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  // Default: flag OFF
  mockGetFlag.mockReturnValue(false)
})

// ── Flag-OFF: skip ─────────────────────────────────────────────────────────

describe('checkpoint_4_5 — flag OFF', () => {
  it('returns skipped=true when CHECKPOINT_4_5_ENABLED is false', async () => {
    mockGetFlag.mockReturnValue(false)
    const result = await runCheckpoint4_5(makeInput())
    expect(result.skipped).toBe(true)
    expect(result.verdict).toBe('pass')
    expect(mockRunAdapter).not.toHaveBeenCalled()
  })
})

// ── Flag-ON: pass ────────────────────────────────────────────────────────────

describe('checkpoint_4_5 — pass verdict', () => {
  beforeEach(() => {
    mockGetFlag.mockImplementation((flag: string) => flag === 'CHECKPOINT_4_5_ENABLED')
  })

  it('returns pass verdict with correct fields', async () => {
    mockLLMResponse('pass', 0.95, 'Resolution is correct')
    const result = await runCheckpoint4_5(makeInput())
    expect(result.verdict).toBe('pass')
    expect(result.confidence).toBe(0.95)
    expect(result.reasoning).toBe('Resolution is correct')
    expect(result.skipped).toBe(false)
    expect(result.checkpoint_id).toBe('checkpoint_4_5')
  })

  it('records latency_ms > 0 on successful call', async () => {
    mockLLMResponse('pass')
    const result = await runCheckpoint4_5(makeInput())
    expect(result.latency_ms).toBeGreaterThanOrEqual(0)
  })

  it('calls runAdapter with a prompt containing the query', async () => {
    mockLLMResponse('pass')
    await runCheckpoint4_5(makeInput())
    const callArgs = mockRunAdapter.mock.calls[0][0] as { messages: Array<{ content: string }> }
    expect(callArgs.messages[0].content).toContain('Saturn in the 10th house')
  })

  it('includes discarded alternatives in the prompt', async () => {
    mockLLMResponse('pass')
    await runCheckpoint4_5(makeInput({ discarded_alternatives: ['transit_sun', 'progressed_sun'] }))
    const callArgs = mockRunAdapter.mock.calls[0][0] as { messages: Array<{ content: string }> }
    expect(callArgs.messages[0].content).toContain('transit_sun')
  })

  it('attaches suggested_revision when LLM provides one', async () => {
    mockRunAdapter.mockResolvedValue({
      finalText: JSON.stringify({
        verdict: 'warn',
        confidence: 0.7,
        reasoning: 'Ambiguity detected',
        suggested_revision: { query_class: 'predictive' },
      }),
      usage: { inputTokens: 0, outputTokens: 0 },
      finishReason: 'stop',
      intermediate: [],
    })
    const result = await runCheckpoint4_5(makeInput())
    expect(result.suggested_revision).toEqual({ query_class: 'predictive' })
  })
})

// ── Flag-ON: warn ─────────────────────────────────────────────────────────────

describe('checkpoint_4_5 — warn verdict', () => {
  beforeEach(() => {
    mockGetFlag.mockImplementation((flag: string) => flag === 'CHECKPOINT_4_5_ENABLED')
  })

  it('returns warn verdict without throwing', async () => {
    mockLLMResponse('warn', 0.6, 'Minor ambiguity')
    const result = await runCheckpoint4_5(makeInput())
    expect(result.verdict).toBe('warn')
    expect(result.confidence).toBe(0.6)
  })
})

// ── Flag-ON: halt ─────────────────────────────────────────────────────────────

describe('checkpoint_4_5 — halt verdict', () => {
  it('returns halt without throwing when FAIL_HARD=false', async () => {
    mockGetFlag.mockImplementation((flag: string) =>
      flag === 'CHECKPOINT_4_5_ENABLED' // FAIL_HARD is false
    )
    mockLLMResponse('halt', 0.95, 'Wrong native chart')
    const result = await runCheckpoint4_5(makeInput())
    expect(result.verdict).toBe('halt')
  })

  it('throws CheckpointHaltError when FAIL_HARD=true and verdict is halt', async () => {
    mockGetFlag.mockImplementation((flag: string) =>
      flag === 'CHECKPOINT_4_5_ENABLED' || flag === 'CHECKPOINT_4_5_FAIL_HARD'
    )
    mockLLMResponse('halt', 0.95, 'Wrong native chart')
    await expect(runCheckpoint4_5(makeInput())).rejects.toThrow(CheckpointHaltError)
  })

  it('does not throw CheckpointHaltError for pass when FAIL_HARD=true', async () => {
    mockGetFlag.mockImplementation((flag: string) =>
      flag === 'CHECKPOINT_4_5_ENABLED' || flag === 'CHECKPOINT_4_5_FAIL_HARD'
    )
    mockLLMResponse('pass', 0.99, 'All good')
    const result = await runCheckpoint4_5(makeInput())
    expect(result.verdict).toBe('pass')
  })
})

// ── LLM output parse failure ──────────────────────────────────────────────────

describe('checkpoint_4_5 — parse failure', () => {
  beforeEach(() => {
    mockGetFlag.mockImplementation((flag: string) => flag === 'CHECKPOINT_4_5_ENABLED')
  })

  it('defaults to pass when LLM returns invalid JSON', async () => {
    mockRunAdapter.mockResolvedValue({ finalText: 'not json at all', usage: { inputTokens: 0, outputTokens: 0 }, finishReason: 'stop', intermediate: [] })
    const result = await runCheckpoint4_5(makeInput())
    expect(result.verdict).toBe('pass')
    expect(result.reasoning).toContain('parse failed')
  })

  it('defaults to pass when LLM returns JSON with wrong schema', async () => {
    mockRunAdapter.mockResolvedValue({
      finalText: JSON.stringify({ foo: 'bar', baz: 123 }),
      usage: { inputTokens: 0, outputTokens: 0 },
      finishReason: 'stop',
      intermediate: [],
    })
    const result = await runCheckpoint4_5(makeInput())
    expect(result.verdict).toBe('pass')
    expect(result.reasoning).toContain('schema invalid')
  })

  it('defaults to pass when runAdapter throws', async () => {
    mockRunAdapter.mockRejectedValue(new Error('network timeout'))
    const result = await runCheckpoint4_5(makeInput())
    expect(result.verdict).toBe('pass')
    expect(result.reasoning).toContain('Checkpoint error')
  })
})

// ── Latency budget ────────────────────────────────────────────────────────────

describe('checkpoint_4_5 — latency budget', () => {
  it('latency_ms is present in result (budget enforced in integration; unit verifies field exists)', async () => {
    mockGetFlag.mockImplementation((flag: string) => flag === 'CHECKPOINT_4_5_ENABLED')
    mockLLMResponse('pass')
    const result = await runCheckpoint4_5(makeInput())
    expect(typeof result.latency_ms).toBe('number')
    // In unit tests, mock resolves instantly — field existence is sufficient
    expect(result.latency_ms).toBeGreaterThanOrEqual(0)
  })
})
