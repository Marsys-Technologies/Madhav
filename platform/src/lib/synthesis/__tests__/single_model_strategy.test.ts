/**
 * Integration tests for §5C checkpoint_dasha retry loop in SingleModelOrchestrator.
 * Covers:
 *   1. Pass on first try — no retry triggered
 *   2. Halt → retry 1 → pass — response shipped with retry count
 *   3. Halt × 3 → CheckpointHaltError when CHECKPOINT_DASHA_FAIL_HARD=true
 *   4. Heuristic-skip — non-dasha query streams normally even with validator enabled
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

vi.mock('@/lib/models/resolver', () => ({
  resolveModel: vi.fn(() => ({ id: 'claude-haiku-4-5', provider: 'anthropic' })),
  isReasoningModel: vi.fn(() => false),
  resolveWorkerModel: vi.fn((id: string) => id ?? 'claude-haiku-4-5'),
  supportsStreaming: vi.fn(() => true),
  googleProviderOptions: vi.fn(() => null),
  deepseekProviderOptions: vi.fn(() => null),
}))

const mockStreamText = vi.fn()
vi.mock('ai', () => ({
  streamText: (...args: unknown[]) => mockStreamText(...args),
  stepCountIs: vi.fn((n: number) => ({ type: 'stepCount', value: n })),
  smoothStream: vi.fn(() => (stream: unknown) => stream),
  tool: vi.fn((config: unknown) => config),
}))

vi.mock('@/lib/models/registry', () => ({
  supports: vi.fn().mockImplementation((_id: string, cap: string) =>
    cap === 'tool-use' || cap === 'prompt-caching',
  ),
  MODELS: [],
  getModelMeta: vi.fn((id: string) => ({
    id,
    label: 'Test Model',
    provider: 'anthropic',
    speedTier: 'fast',
    maxOutputTokens: 64000,
    capabilities: ['tool-use', 'prompt-caching'],
  })),
  getReasoningMode: vi.fn(() => 'none'),
}))

vi.mock('@/lib/retrieve/index', () => ({
  getTool: vi.fn((name: string) => ({
    name,
    version: '1.0',
    retrieve: vi.fn().mockResolvedValue({ results: [], tool_name: name }),
  })),
}))

vi.mock('@/lib/validators/index', () => ({
  runAll: vi.fn().mockResolvedValue([]),
}))

vi.mock('@/lib/cache/index', () => ({
  executeWithCache: vi.fn().mockResolvedValue({
    tool_bundle_id: 'test-bundle',
    tool_name: 'msr_sql',
    tool_version: '1.0',
    invocation_params: {},
    results: [],
    served_from_cache: false,
    latency_ms: 10,
    result_hash: 'sha256:abc',
    schema_version: '1.0' as const,
  }),
  createToolCache: vi.fn(),
}))

vi.mock('@/lib/telemetry/index', () => ({
  telemetry: {
    recordMetric: vi.fn(),
    recordLatency: vi.fn(),
    recordError: vi.fn(),
  },
}))

// ── Checkpoint dasha mock — we test the retry loop, not the validator logic ──
const mockRunCheckpointDasha = vi.fn()
const mockDetectDashaRelevance = vi.fn()
const mockBuildDashaRemediationPrompt = vi.fn().mockResolvedValue('\n\nDASHA REMEDIATION: ...')
vi.mock('@/lib/checkpoints/checkpoint_dasha', () => ({
  runCheckpointDasha: (...args: unknown[]) => mockRunCheckpointDasha(...args),
  detectDashaRelevance: (...args: unknown[]) => mockDetectDashaRelevance(...args),
  buildDashaRemediationPrompt: (...args: unknown[]) => mockBuildDashaRemediationPrompt(...args),
}))

const mockGetFlag = vi.fn()
vi.mock('@/lib/config/index', () => ({
  getFlag: (...args: unknown[]) => mockGetFlag(...args),
  configService: { getFlag: (...args: unknown[]) => mockGetFlag(...args) },
}))

// Stub all other internal deps
vi.mock('@/lib/prompts/index', () => ({
  getDefaultRegistry: vi.fn(() => ({
    get: vi.fn(() => ({
      version: '3.1',
      render: vi.fn(() => 'System prompt for {{chart_name}}'),
    })),
  })),
}))
vi.mock('@/lib/prompts/types', () => ({
  renderTemplate: vi.fn((_t: unknown, vars: Record<string, string>) =>
    `SYSTEM: chart_name=${vars.chart_name}`,
  ),
}))
vi.mock('@/lib/synthesis/citation_check', () => ({ countSignalCitations: vi.fn(() => 0) }))
vi.mock('@/lib/synthesis/b11_guard', () => ({
  checkB11Compliance: vi.fn(() => ({ compliant: true, missingLayers: [], presentLayers: [] })),
}))
vi.mock('@/lib/synthesis/prompts/synthesis_prompt_v2', () => ({ CITATION_APPENDIX: '' }))
vi.mock('@/lib/synthesis/provider_quirks', () => ({ getMaxRetries: vi.fn(() => 1) }))
vi.mock('@/lib/synthesis/token_caps', () => ({
  STYLE_OUTPUT_CAP: { acharya: 8000, client: 3500, brief: 1200 },
  CLASS_TOKEN_CAP: {},
  computeEffectiveMaxTokens: vi.fn((a: number) => a),
}))
vi.mock('@/lib/prompts/templates/shared', () => ({
  REASONING_NARRATION_GATE: '',
}))
vi.mock('@/lib/db/monitoring-write', () => ({
  writeLlmCallLog: vi.fn(),
  resolveProvider: vi.fn(() => 'anthropic'),
}))
vi.mock('@/lib/llm/pricing', () => ({
  computeCostUsd: vi.fn(() => 0),
  getModelPricingSync: vi.fn(() => ({ input_per_mtok: 0, output_per_mtok: 0 })),
}))
vi.mock('@/lib/llm/observability', () => ({
  persistObservation: vi.fn(),
  computeCost: vi.fn(() => 0),
}))
vi.mock('@/lib/storage', () => ({
  getStorageClient: vi.fn(() => ({ query: vi.fn().mockResolvedValue({ rows: [] }) })),
}))
vi.mock('@/lib/trace/emitter', () => ({
  traceEmitter: { emitStep: vi.fn() },
}))

import { SingleModelOrchestrator } from '../single_model_strategy'
import { CheckpointHaltError } from '@/lib/checkpoints/types'
import type { SynthesisRequest } from '../types'

function makeRequest(
  queryOverride = 'What is my current mahadasha?',
): SynthesisRequest {
  return {
    query: queryOverride,
    query_plan: {
      query_plan_id: 'plan-uuid-001',
      query_text: queryOverride,
      query_class: 'predictive',
      domains: ['temporal'],
      forward_looking: true,
      audience_tier: 'super_admin',
      tools_authorized: ['query_dasha_periods'],
      history_mode: 'synthesized',
      panel_mode: false,
      expected_output_shape: 'time_indexed_prediction',
      manifest_fingerprint: 'fp-test-abc123',
      schema_version: '1.0',
    },
    bundle: {
      bundle_id: 'bundle-uuid-001',
      query_plan_reference: 'plan-uuid-001',
      manifest_fingerprint: 'fp-test-abc123',
      mandatory_context: [
        {
          canonical_id: 'FORENSIC',
          version: '8.0',
          content_hash: 'sha256:aaa',
          token_count: 1000,
          role: 'floor',
          source: 'rule_composer',
        },
      ],
      total_tokens: 1000,
      bundle_hash: 'sha256:bundle-hash-xyz',
      schema_version: '1.0',
    },
    tool_results: [],
    conversation_history: [],
    selected_model_id: 'claude-haiku-4-5',
    style: 'acharya',
    audience_tier: 'super_admin',
    cache: {
      get: vi.fn(),
      put: vi.fn(),
      getPromise: vi.fn().mockReturnValue(undefined),
      generateKey: vi.fn().mockReturnValue('test-key'),
      clear: vi.fn(),
      size: vi.fn().mockReturnValue(0),
    } as unknown as import('@/lib/cache/index').RequestScopedToolCache,
  }
}

function makeMockStreamResult(text = 'The next MD is Ketu (→ DSH.V.024, ...).') {
  return {
    toUIMessageStreamResponse: vi.fn(),
    toUIMessageStream: vi.fn(),
    consumeStream: vi.fn(),
    textStream: {},
    text: Promise.resolve(text),
  }
}

function passResult() {
  return {
    checkpoint_id: 'checkpoint_dasha',
    verdict: 'pass' as const,
    confidence: 1,
    reasoning: 'All claims passed',
    latency_ms: 5,
    skipped: false,
    claims: [],
    claims_extracted: 0,
    violations_count: 0,
  }
}

function haltResult() {
  return {
    checkpoint_id: 'checkpoint_dasha',
    verdict: 'halt' as const,
    confidence: 0,
    reasoning: '1 violation: temporal_claim_no_citation',
    latency_ms: 5,
    skipped: false,
    claims: [
      {
        span: 'next MD is Saturn',
        start: 0,
        end: 17,
        temporal: 'next' as const,
        lord: 'Saturn',
        level: 'MD' as const,
        has_citation: false,
        cited_fact_id: null,
        cited_date_range: null,
        verdict: 'halt' as const,
        violation: 'temporal_claim_no_citation',
      },
    ],
    claims_extracted: 1,
    violations_count: 1,
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  // Default: all flags OFF
  mockGetFlag.mockReturnValue(false)
  mockDetectDashaRelevance.mockReturnValue(false)
})

// ─────────────────────────────────────────────────────────────────────────────
// Test 1: Pass on first try — no retry triggered
// ─────────────────────────────────────────────────────────────────────────────

describe('checkpoint_dasha retry loop — pass on first try', () => {
  it('calls streamText once and returns result when validator passes', async () => {
    mockGetFlag.mockImplementation((flag: string) =>
      flag === 'CHECKPOINT_DASHA_ENABLED' || flag === 'CHECKPOINT_DASHA_FAIL_HARD',
    )
    mockDetectDashaRelevance.mockReturnValue(true)
    mockRunCheckpointDasha.mockResolvedValue(passResult())

    const mockResult = makeMockStreamResult()
    mockStreamText.mockReturnValue(mockResult)

    const orchestrator = new SingleModelOrchestrator()
    const { result } = await orchestrator.synthesize(makeRequest())

    expect(mockStreamText).toHaveBeenCalledTimes(1)
    expect(mockRunCheckpointDasha).toHaveBeenCalledTimes(1)
    expect(result).toBe(mockResult)
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// Test 2: Halt → retry 1 → pass
// ─────────────────────────────────────────────────────────────────────────────

describe('checkpoint_dasha retry loop — halt then pass on retry', () => {
  it('calls streamText twice and returns second result when first halts but retry passes', async () => {
    mockGetFlag.mockImplementation((flag: string) =>
      flag === 'CHECKPOINT_DASHA_ENABLED' || flag === 'CHECKPOINT_DASHA_FAIL_HARD',
    )
    mockDetectDashaRelevance.mockReturnValue(true)
    // First call halts (FAIL_HARD=true so throws)
    mockRunCheckpointDasha
      .mockRejectedValueOnce(new CheckpointHaltError('checkpoint_dasha', haltResult()))
      .mockResolvedValueOnce(passResult())

    const firstResult = makeMockStreamResult('The next MD is Saturn.')
    const secondResult = makeMockStreamResult('Next Ketu MD (→ DSH.V.024, 2027-08-21).')
    mockStreamText.mockReturnValueOnce(firstResult).mockReturnValueOnce(secondResult)

    const orchestrator = new SingleModelOrchestrator()
    const { result } = await orchestrator.synthesize(makeRequest())

    expect(mockStreamText).toHaveBeenCalledTimes(2)
    expect(mockRunCheckpointDasha).toHaveBeenCalledTimes(2)
    expect(result).toBe(secondResult)
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// Test 3: Halt × 3 → throws CheckpointHaltError
// ─────────────────────────────────────────────────────────────────────────────

describe('checkpoint_dasha retry loop — halt exhausts retries', () => {
  it('throws CheckpointHaltError after MAX_RETRIES when CHECKPOINT_DASHA_FAIL_HARD=true', async () => {
    mockGetFlag.mockImplementation((flag: string) =>
      flag === 'CHECKPOINT_DASHA_ENABLED' || flag === 'CHECKPOINT_DASHA_FAIL_HARD',
    )
    mockDetectDashaRelevance.mockReturnValue(true)
    // All 3 attempts (attempt 0, 1, 2) halt
    const haltErr = new CheckpointHaltError('checkpoint_dasha', haltResult())
    mockRunCheckpointDasha
      .mockRejectedValueOnce(haltErr)
      .mockRejectedValueOnce(haltErr)
      .mockRejectedValueOnce(haltErr)

    const streamRes = makeMockStreamResult('The next MD is Saturn.')
    mockStreamText.mockReturnValue(streamRes)

    const orchestrator = new SingleModelOrchestrator()
    await expect(orchestrator.synthesize(makeRequest())).rejects.toBeInstanceOf(
      CheckpointHaltError,
    )
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// Test 4: Heuristic-skip — non-dasha query streams normally
// ─────────────────────────────────────────────────────────────────────────────

describe('checkpoint_dasha retry loop — heuristic skip', () => {
  it('does not call runCheckpointDasha for a non-dasha query even when flag is ON', async () => {
    mockGetFlag.mockImplementation((flag: string) =>
      flag === 'CHECKPOINT_DASHA_ENABLED' || flag === 'CHECKPOINT_DASHA_FAIL_HARD',
    )
    // detectDashaRelevance returns false for this query
    mockDetectDashaRelevance.mockReturnValue(false)

    const mockResult = makeMockStreamResult('Saturn in 10th house creates Shasha yoga.')
    mockStreamText.mockReturnValue(mockResult)

    const orchestrator = new SingleModelOrchestrator()
    const request = makeRequest("What is my Saturn's dignity in D1?")
    const { result } = await orchestrator.synthesize(request)

    expect(mockRunCheckpointDasha).not.toHaveBeenCalled()
    expect(mockStreamText).toHaveBeenCalledTimes(1)
    expect(result).toBe(mockResult)
  })
})
