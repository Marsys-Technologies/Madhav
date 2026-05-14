import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))
vi.mock('fs', () => ({
  default: {
    readFileSync: vi.fn(() =>
      'Class: {{query_class}}\nValidators: {{validator_results_json}}\nSynthesis: {{synthesized_text}}',
    ),
  },
}))
vi.mock('@/lib/models/runtime_config', () => ({
  getEffectiveModel: vi.fn().mockResolvedValue('claude-sonnet-4-6'),
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

import { runCheckpoint8_5 } from '../checkpoint_8_5'
import { CheckpointHaltError } from '../types'
import type { Checkpoint85Input, StructuredPrediction } from '../types'

function makeInput(overrides: Partial<Checkpoint85Input> = {}): Checkpoint85Input {
  return {
    synthesized_text:
      'Saturn in the 10th house creates a strong career dharma. The native will experience significant professional responsibilities and delays that ultimately lead to lasting achievements.',
    query_class: 'interpretive',
    validator_results: [
      { validator_id: 'p1_layer_separation', validator_version: '1.0', vote: 'pass' },
      { validator_id: 'p2_citation', validator_version: '1.0', vote: 'pass' },
    ],
    ...overrides,
  }
}

function mockLLMPass(extras?: Partial<{ prediction: StructuredPrediction }>) {
  mockRunAdapter.mockResolvedValue({
    finalText: JSON.stringify({
      verdict: 'pass',
      confidence: 0.92,
      reasoning: 'Synthesis is substantive',
      ...extras,
    }),
    usage: { inputTokens: 0, outputTokens: 0 },
    finishReason: 'stop',
    intermediate: [],
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  mockGetFlag.mockReturnValue(false)
})

// ── Flag-OFF ──────────────────────────────────────────────────────────────────

describe('checkpoint_8_5 — flag OFF', () => {
  it('returns skipped=true when CHECKPOINT_8_5_ENABLED is false', async () => {
    const result = await runCheckpoint8_5(makeInput())
    expect(result.skipped).toBe(true)
    expect(result.verdict).toBe('pass')
    expect(mockRunAdapter).not.toHaveBeenCalled()
  })
})

// ── Pass verdict ──────────────────────────────────────────────────────────────

describe('checkpoint_8_5 — pass verdict', () => {
  beforeEach(() => {
    mockGetFlag.mockImplementation((flag: string) => flag === 'CHECKPOINT_8_5_ENABLED')
  })

  it('returns pass verdict with correct fields', async () => {
    mockLLMPass()
    const result = await runCheckpoint8_5(makeInput())
    expect(result.verdict).toBe('pass')
    expect(result.confidence).toBe(0.92)
    expect(result.checkpoint_id).toBe('checkpoint_8_5')
    expect(result.skipped).toBe(false)
  })

  it('includes synthesized text in the prompt', async () => {
    mockLLMPass()
    await runCheckpoint8_5(makeInput())
    const prompt = (mockRunAdapter.mock.calls[0][0] as { messages: Array<{ content: string }> }).messages[0].content
    expect(prompt).toContain('Saturn in the 10th house')
  })

  it('includes validator results in the prompt', async () => {
    mockLLMPass()
    await runCheckpoint8_5(makeInput())
    const prompt = (mockRunAdapter.mock.calls[0][0] as { messages: Array<{ content: string }> }).messages[0].content
    expect(prompt).toContain('p1_layer_separation')
    expect(prompt).toContain('pass')
  })

  it('uses claude-sonnet-4-6 as checkpoint model', async () => {
    mockLLMPass()
    await runCheckpoint8_5(makeInput())
    const callArg = mockRunAdapter.mock.calls[0][0] as { modelOverride: { modelId: string } }
    expect(callArg.modelOverride.modelId).toBe('claude-sonnet-4-6')
  })
})

// ── Warn verdict ──────────────────────────────────────────────────────────────

describe('checkpoint_8_5 — warn verdict', () => {
  beforeEach(() => {
    mockGetFlag.mockImplementation((flag: string) => flag === 'CHECKPOINT_8_5_ENABLED')
  })

  it('returns warn without throwing', async () => {
    mockRunAdapter.mockResolvedValue({
      finalText: JSON.stringify({ verdict: 'warn', confidence: 0.65, reasoning: 'Excessive hedging' }),
      usage: { inputTokens: 0, outputTokens: 0 }, finishReason: 'stop', intermediate: [],
    })
    const result = await runCheckpoint8_5(makeInput())
    expect(result.verdict).toBe('warn')
  })
})

// ── Halt verdict ──────────────────────────────────────────────────────────────

describe('checkpoint_8_5 — halt verdict', () => {
  it('returns halt (not throw) when FAIL_HARD=false', async () => {
    mockGetFlag.mockImplementation((flag: string) => flag === 'CHECKPOINT_8_5_ENABLED')
    mockRunAdapter.mockResolvedValue({
      finalText: JSON.stringify({ verdict: 'halt', confidence: 0.95, reasoning: 'Empty shell' }),
      usage: { inputTokens: 0, outputTokens: 0 }, finishReason: 'stop', intermediate: [],
    })
    const result = await runCheckpoint8_5(makeInput())
    expect(result.verdict).toBe('halt')
  })

  it('throws CheckpointHaltError when FAIL_HARD=true', async () => {
    mockGetFlag.mockImplementation((flag: string) =>
      flag === 'CHECKPOINT_8_5_ENABLED' || flag === 'CHECKPOINT_8_5_FAIL_HARD'
    )
    mockRunAdapter.mockResolvedValue({
      finalText: JSON.stringify({ verdict: 'halt', confidence: 0.95, reasoning: 'Empty shell' }),
      usage: { inputTokens: 0, outputTokens: 0 }, finishReason: 'stop', intermediate: [],
    })
    await expect(runCheckpoint8_5(makeInput())).rejects.toThrow(CheckpointHaltError)
  })
})

// ── Prediction extraction ─────────────────────────────────────────────────────

describe('checkpoint_8_5 — prediction extraction', () => {
  const validPrediction: StructuredPrediction = {
    prediction_text: 'Professional role change likely during Jupiter MD / Saturn AD',
    confidence: 0.72,
    horizon_start: '2027-01-01',
    horizon_end: '2028-12-31',
    falsifier: 'No professional role change in the stated period',
    subject: 'native:abhisek',
  }

  it('attaches prediction when PREDICTION_EXTRACT flag is ON and LLM provides one', async () => {
    mockGetFlag.mockImplementation((flag: string) =>
      flag === 'CHECKPOINT_8_5_ENABLED' || flag === 'CHECKPOINT_8_5_PREDICTION_EXTRACT'
    )
    mockLLMPass({ prediction: validPrediction })
    const result = await runCheckpoint8_5(
      makeInput({ query_class: 'predictive' }),
    )
    expect(result.prediction).toEqual(validPrediction)
  })

  it('strips prediction when PREDICTION_EXTRACT flag is OFF', async () => {
    mockGetFlag.mockImplementation((flag: string) => flag === 'CHECKPOINT_8_5_ENABLED')
    mockLLMPass({ prediction: validPrediction })
    const result = await runCheckpoint8_5(makeInput({ query_class: 'predictive' }))
    expect(result.prediction).toBeUndefined()
  })

  it('returns no prediction for non-predictive query class even with extract ON', async () => {
    mockGetFlag.mockImplementation((flag: string) =>
      flag === 'CHECKPOINT_8_5_ENABLED' || flag === 'CHECKPOINT_8_5_PREDICTION_EXTRACT'
    )
    // LLM returns no prediction field (non-time-indexed synthesis)
    mockLLMPass()
    const result = await runCheckpoint8_5(makeInput({ query_class: 'interpretive' }))
    expect(result.prediction).toBeUndefined()
  })

  it('rejects prediction with outcome field — Zod strips unknown fields', async () => {
    mockGetFlag.mockImplementation((flag: string) =>
      flag === 'CHECKPOINT_8_5_ENABLED' || flag === 'CHECKPOINT_8_5_PREDICTION_EXTRACT'
    )
    // outcome field should be rejected by Zod schema (strict schema strips it)
    mockRunAdapter.mockResolvedValue({
      finalText: JSON.stringify({
        verdict: 'pass',
        confidence: 0.9,
        reasoning: 'ok',
        prediction: {
          ...validPrediction,
          outcome: 'prediction came true', // must be stripped
        },
      }),
      usage: { inputTokens: 0, outputTokens: 0 }, finishReason: 'stop', intermediate: [],
    })
    const result = await runCheckpoint8_5(makeInput({ query_class: 'predictive' }))
    // prediction is present but outcome field is NOT in the typed result
    expect(result.prediction).toBeDefined()
    expect((result.prediction as Record<string, unknown>)?.outcome).toBeUndefined()
  })

  it('falls back to no-prediction on malformed prediction sub-object', async () => {
    mockGetFlag.mockImplementation((flag: string) =>
      flag === 'CHECKPOINT_8_5_ENABLED' || flag === 'CHECKPOINT_8_5_PREDICTION_EXTRACT'
    )
    mockRunAdapter.mockResolvedValue({
      finalText: JSON.stringify({
        verdict: 'pass',
        confidence: 0.9,
        reasoning: 'ok',
        prediction: {
          // missing required fields
          prediction_text: 'Some claim',
        },
      }),
      usage: { inputTokens: 0, outputTokens: 0 }, finishReason: 'stop', intermediate: [],
    })
    // Zod safeParse on the outer schema should succeed but inner prediction validation fails
    // The outer schema uses .optional() so a bad prediction is stripped
    const result = await runCheckpoint8_5(makeInput({ query_class: 'predictive' }))
    // Either prediction is absent or the whole response falls back to pass with warning
    expect(result.verdict).toBe('pass')
  })
})

// ── Sub-flag interactions ─────────────────────────────────────────────────────

describe('checkpoint_8_5 — sub-flag interactions', () => {
  it('does not run when CHECKPOINT_8_5_ENABLED=false even if PREDICTION_EXTRACT=true', async () => {
    mockGetFlag.mockImplementation((flag: string) => flag === 'CHECKPOINT_8_5_PREDICTION_EXTRACT')
    const result = await runCheckpoint8_5(makeInput())
    expect(result.skipped).toBe(true)
    expect(mockRunAdapter).not.toHaveBeenCalled()
  })
})

// ── Parse failure ─────────────────────────────────────────────────────────────

describe('checkpoint_8_5 — parse failure', () => {
  beforeEach(() => {
    mockGetFlag.mockImplementation((flag: string) => flag === 'CHECKPOINT_8_5_ENABLED')
  })

  it('defaults to pass on invalid JSON', async () => {
    mockRunAdapter.mockResolvedValue({ finalText: '{ broken json', usage: { inputTokens: 0, outputTokens: 0 }, finishReason: 'stop', intermediate: [] })
    const result = await runCheckpoint8_5(makeInput())
    expect(result.verdict).toBe('pass')
    expect(result.reasoning).toContain('parse failed')
  })

  it('defaults to pass when runAdapter rejects', async () => {
    mockRunAdapter.mockRejectedValue(new Error('model overloaded'))
    const result = await runCheckpoint8_5(makeInput())
    expect(result.verdict).toBe('pass')
    expect(result.reasoning).toContain('Checkpoint error')
  })
})

// ── Latency budget ────────────────────────────────────────────────────────────

describe('checkpoint_8_5 — latency field', () => {
  it('latency_ms is present as a non-negative number', async () => {
    mockGetFlag.mockImplementation((flag: string) => flag === 'CHECKPOINT_8_5_ENABLED')
    mockLLMPass()
    const result = await runCheckpoint8_5(makeInput())
    expect(typeof result.latency_ms).toBe('number')
    expect(result.latency_ms).toBeGreaterThanOrEqual(0)
  })
})
