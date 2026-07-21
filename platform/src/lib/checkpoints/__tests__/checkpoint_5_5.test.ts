import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))
vi.mock('fs', () => ({
  default: {
    readFileSync: vi.fn(() =>
      'Query: {{query}}\nClass: {{query_class}}\nAssets: {{bundle_assets}}\nSignals: {{signals_preview}}',
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

import { runCheckpoint5_5 } from '../checkpoint_5_5'
import { CheckpointHaltError } from '../types'
import type { Checkpoint55Input } from '../types'

function makeInput(overrides: Partial<Checkpoint55Input> = {}): Checkpoint55Input {
  return {
    query: 'What are the patterns across career and relationships in my chart?',
    query_plan: {
      query_plan_id: 'plan-002',
      query_text: 'What are the patterns across career and relationships in my chart?',
      query_class: 'cross_domain',
      domains: ['career', 'relationships'],
      forward_looking: false,
      tools_authorized: ['msr_sql', 'pattern_register'],
      history_mode: 'synthesized',
      panel_mode: false,
      expected_output_shape: 'three_interpretation',
      manifest_fingerprint: 'fp-abc',
      schema_version: '1.0',
    },
    bundle: {
      bundle_id: 'bundle-002',
      query_plan_reference: 'plan-002',
      manifest_fingerprint: 'fp-abc',
      mandatory_context: [
        {
          canonical_id: 'FORENSIC',
          version: '8.0',
          content_hash: 'sha256:aaa',
          token_count: 1000,
          role: 'floor',
          source: 'rule_composer',
        },
        {
          canonical_id: 'MSR',
          version: '3.0',
          content_hash: 'sha256:bbb',
          token_count: 500,
          role: 'interpretive',
          source: 'rule_composer',
        },
      ],
      total_tokens: 1500,
      bundle_hash: 'sha256:xyz',
      schema_version: '1.0',
    },
    tool_results: [
      {
        tool_bundle_id: 'tb-001',
        tool_name: 'msr_sql',
        tool_version: '1.0',
        invocation_params: {},
        results: [
          {
            content: 'Saturn in 10th house — career discipline signal',
            signal_id: 'MSR-0042',
            confidence: 0.9,
            significance: 0.85,
          },
        ],
        served_from_cache: false,
        latency_ms: 50,
        result_hash: 'sha256:ccc',
        schema_version: '1.0' as const,
      },
    ],
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
  mockGetFlag.mockReturnValue(false)
})

// ── Flag-OFF ──────────────────────────────────────────────────────────────────

describe('checkpoint_5_5 — flag OFF', () => {
  it('returns skipped=true when CHECKPOINT_5_5_ENABLED is false', async () => {
    const result = await runCheckpoint5_5(makeInput())
    expect(result.skipped).toBe(true)
    expect(result.verdict).toBe('pass')
    expect(mockRunAdapter).not.toHaveBeenCalled()
  })
})

// ── Pass verdict ──────────────────────────────────────────────────────────────

describe('checkpoint_5_5 — pass verdict', () => {
  beforeEach(() => {
    mockGetFlag.mockImplementation((flag: string) => flag === 'CHECKPOINT_5_5_ENABLED')
  })

  it('returns pass verdict with correct fields', async () => {
    mockLLMResponse('pass', 0.92, 'Bundle is sufficient')
    const result = await runCheckpoint5_5(makeInput())
    expect(result.verdict).toBe('pass')
    expect(result.confidence).toBe(0.92)
    expect(result.reasoning).toBe('Bundle is sufficient')
    expect(result.checkpoint_id).toBe('checkpoint_5_5')
    expect(result.skipped).toBe(false)
  })

  it('includes bundle asset info in the prompt', async () => {
    mockLLMResponse('pass')
    await runCheckpoint5_5(makeInput())
    const prompt = (mockRunAdapter.mock.calls[0][0] as { messages: Array<{ content: string }> }).messages[0].content
    expect(prompt).toContain('FORENSIC')
    expect(prompt).toContain('floor')
  })

  it('includes signal_id in signals preview', async () => {
    mockLLMResponse('pass')
    await runCheckpoint5_5(makeInput())
    const prompt = (mockRunAdapter.mock.calls[0][0] as { messages: Array<{ content: string }> }).messages[0].content
    expect(prompt).toContain('MSR-0042')
  })

  it('includes query class in prompt', async () => {
    mockLLMResponse('pass')
    await runCheckpoint5_5(makeInput())
    const prompt = (mockRunAdapter.mock.calls[0][0] as { messages: Array<{ content: string }> }).messages[0].content
    expect(prompt).toContain('cross_domain')
  })
})

// ── Warn verdict ──────────────────────────────────────────────────────────────

describe('checkpoint_5_5 — warn verdict', () => {
  beforeEach(() => {
    mockGetFlag.mockImplementation((flag: string) => flag === 'CHECKPOINT_5_5_ENABLED')
  })

  it('returns warn with missing_signal_hints', async () => {
    mockRunAdapter.mockResolvedValue({
      finalText: JSON.stringify({
        verdict: 'warn',
        confidence: 0.6,
        reasoning: 'Relationship signals absent',
        missing_signal_hints: ['relationship domain signals', 'Venus placement signals'],
      }),
      usage: { inputTokens: 0, outputTokens: 0 },
      finishReason: 'stop',
      intermediate: [],
    })
    const result = await runCheckpoint5_5(makeInput())
    expect(result.verdict).toBe('warn')
    expect(result.missing_signal_hints).toEqual([
      'relationship domain signals',
      'Venus placement signals',
    ])
  })

  it('missing_signal_hints is undefined when LLM does not provide them', async () => {
    mockLLMResponse('warn', 0.7, 'Thin but adequate')
    const result = await runCheckpoint5_5(makeInput())
    expect(result.missing_signal_hints).toBeUndefined()
  })
})

// ── Halt verdict ──────────────────────────────────────────────────────────────

describe('checkpoint_5_5 — halt verdict', () => {
  it('returns halt without throwing when FAIL_HARD=false', async () => {
    mockGetFlag.mockImplementation((flag: string) => flag === 'CHECKPOINT_5_5_ENABLED')
    mockLLMResponse('halt', 0.95, 'Bundle critically empty')
    const result = await runCheckpoint5_5(makeInput())
    expect(result.verdict).toBe('halt')
  })

  it('throws CheckpointHaltError when FAIL_HARD=true and verdict is halt', async () => {
    mockGetFlag.mockImplementation((flag: string) =>
      flag === 'CHECKPOINT_5_5_ENABLED' || flag === 'CHECKPOINT_5_5_FAIL_HARD'
    )
    mockLLMResponse('halt', 0.95, 'Bundle critically empty')
    await expect(runCheckpoint5_5(makeInput())).rejects.toThrow(CheckpointHaltError)
  })
})

// ── Bundle truncation ─────────────────────────────────────────────────────────

describe('checkpoint_5_5 — bundle-too-large truncation', () => {
  it('handles a large number of tool results without crashing', async () => {
    mockGetFlag.mockImplementation((flag: string) => flag === 'CHECKPOINT_5_5_ENABLED')
    mockLLMResponse('pass')
    const manyResults = Array.from({ length: 50 }, (_, i) => ({
      tool_bundle_id: `tb-${i}`,
      tool_name: 'msr_sql',
      tool_version: '1.0',
      invocation_params: {},
      results: [{ content: `Signal content ${i}`, signal_id: `MSR-${i}` }],
      served_from_cache: false,
      latency_ms: 10,
      result_hash: `sha256:${i}`,
      schema_version: '1.0' as const,
    }))
    const result = await runCheckpoint5_5(makeInput({ tool_results: manyResults }))
    expect(result.verdict).toBe('pass')
  })
})

// ── Parse failure ─────────────────────────────────────────────────────────────

describe('checkpoint_5_5 — parse failure', () => {
  beforeEach(() => {
    mockGetFlag.mockImplementation((flag: string) => flag === 'CHECKPOINT_5_5_ENABLED')
  })

  it('defaults to pass on invalid JSON', async () => {
    mockRunAdapter.mockResolvedValue({ finalText: 'not json', usage: { inputTokens: 0, outputTokens: 0 }, finishReason: 'stop', intermediate: [] })
    const result = await runCheckpoint5_5(makeInput())
    expect(result.verdict).toBe('pass')
    expect(result.reasoning).toContain('parse failed')
  })

  it('defaults to pass when runAdapter throws', async () => {
    mockRunAdapter.mockRejectedValue(new Error('timeout'))
    const result = await runCheckpoint5_5(makeInput())
    expect(result.verdict).toBe('pass')
    expect(result.reasoning).toContain('Checkpoint error')
  })
})
