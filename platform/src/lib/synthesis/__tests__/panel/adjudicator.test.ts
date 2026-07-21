import { describe, it, expect, vi, beforeEach } from 'vitest'

// ── Module mocks ──────────────────────────────────────────────────────────────
vi.mock('server-only', () => ({}))

const mockRunAdapter = vi.fn()
vi.mock('@/lib/adapters', () => ({
  runAdapter: (...args: unknown[]) => mockRunAdapter(...args),
}))

vi.mock('@/lib/telemetry/index', () => ({
  telemetry: {
    recordMetric: vi.fn(),
    recordLatency: vi.fn(),
    recordError: vi.fn(),
  },
}))

vi.mock('../../panel/prompt_loader', () => ({
  loadPanelMemberPrompt: vi.fn(() => 'test member prompt'),
  loadAdjudicatorPrompt: vi.fn(() => 'safe adjudicator prompt with no provider names'),
}))

// default_slate is NOT mocked — we test its real interaction with adjudicator

// ── Imports (after mocks) ─────────────────────────────────────────────────────
import {
  adjudicate,
  anonymizePanelOutputs,
  assertNoModelNamesInPrompt,
} from '../../panel/adjudicator'
import { loadAdjudicatorPrompt } from '../../panel/prompt_loader'
import type { PanelMemberConfig, PanelMemberOutput } from '../../panel/types'
import type { SynthesisRequest } from '../../types'

// ── Fixtures ──────────────────────────────────────────────────────────────────

const fakeSynthesisRequest: SynthesisRequest = {
  query: 'What does my 7th house indicate?',
  query_plan: {
    query_class: 'interpretive',
    query_plan_id: 'qp-1',
    tools_authorized: [],
    query_text: 'What does my 7th house indicate?',
    domains: ['relationship'],
    forward_looking: false,
    history_mode: 'synthesized',
    panel_mode: true,
    expected_output_shape: 'three_interpretation',
    manifest_fingerprint: 'fp-test',
    schema_version: '1.0',
  },
  bundle: {
    bundle_id: 'b-1',
    bundle_hash: 'hash',
    mandatory_context: [],
    query_plan_reference: 'qp-1',
    manifest_fingerprint: 'fp-test',
    total_tokens: 0,
    schema_version: '1.0',
  },
  tool_results: [],
  conversation_history: [],
  selected_model_id: 'claude-sonnet-4-6',
  style: 'acharya',
  audience_tier: 'super_admin',
  cache: {} as SynthesisRequest['cache'],
}

const threeSuccessOutputs: PanelMemberOutput[] = [
  { member_index: 0, model_id: 'claude-sonnet-4-6', provider_family: 'anthropic', status: 'success', answer: 'Anthropic answer about 7th house', latency_ms: 1200 },
  { member_index: 1, model_id: 'gpt-4.1',            provider_family: 'openai',    status: 'success', answer: 'OpenAI answer about 7th house',    latency_ms: 900  },
  { member_index: 2, model_id: 'gemini-2.5-pro',     provider_family: 'google',    status: 'success', answer: 'Google answer about 7th house',    latency_ms: 1500 },
]

const threeMembers: PanelMemberConfig[] = [
  { provider_family: 'anthropic', model_id: 'claude-sonnet-4-6' },
  { provider_family: 'openai',    model_id: 'gpt-4.1'            },
  { provider_family: 'google',    model_id: 'gemini-2.5-pro'     },
]

function makeValidAdjudicatorJson(overrides: Record<string, unknown> = {}): string {
  return JSON.stringify({
    final_answer: 'The 7th house indicates partnerships.',
    divergence_summary: {
      has_divergence: false,
      divergence_count: 0,
      summary_text: 'All members aligned.',
    },
    member_alignment: {
      'Member 1': 'aligned',
      'Member 2': 'aligned',
      'Member 3': 'aligned',
    },
    ...overrides,
  })
}

beforeEach(() => {
  vi.clearAllMocks()
})

// ── Tests: family exclusion ────────────────────────────────────────────────────

describe('adjudicate — family exclusion', () => {
  it('resolves the adjudicator model from the deepseek family when slate is anthropic+openai+google', async () => {
    mockRunAdapter.mockResolvedValue({ finalText: makeValidAdjudicatorJson(), usage: { inputTokens: 0, outputTokens: 0 }, finishReason: 'stop', intermediate: [] })

    await adjudicate(threeSuccessOutputs, fakeSynthesisRequest, threeMembers)

    // runAdapter should have been called with the deepseek adjudicator model
    const callArg = mockRunAdapter.mock.calls[0][0] as { modelOverride: { modelId: string } }
    expect(callArg.modelOverride.modelId).toBe('deepseek-chat')
  })
})

// ── Tests: anonymization ──────────────────────────────────────────────────────

describe('anonymizePanelOutputs', () => {
  it('strips model_id and provider_family — output has only member_label, answer, latency_ms', () => {
    const anon = anonymizePanelOutputs(threeSuccessOutputs)
    for (const item of anon) {
      expect(item).not.toHaveProperty('model_id')
      expect(item).not.toHaveProperty('provider_family')
      expect(item).not.toHaveProperty('member_index')
      expect(item).toHaveProperty('member_label')
      expect(item).toHaveProperty('answer')
      expect(item).toHaveProperty('latency_ms')
    }
  })

  it('labels outputs as "Member 1", "Member 2", "Member 3"', () => {
    const anon = anonymizePanelOutputs(threeSuccessOutputs)
    expect(anon[0].member_label).toBe('Member 1')
    expect(anon[1].member_label).toBe('Member 2')
    expect(anon[2].member_label).toBe('Member 3')
  })

  it('excludes failed members from anonymized output', () => {
    const withFailed: PanelMemberOutput[] = [
      ...threeSuccessOutputs.slice(0, 2),
      { member_index: 2, model_id: 'gemini-2.5-pro', provider_family: 'google', status: 'failed', error: 'timeout', latency_ms: 0 },
    ]
    const anon = anonymizePanelOutputs(withFailed)
    expect(anon).toHaveLength(2)
    expect(anon[0].member_label).toBe('Member 1')
    expect(anon[1].member_label).toBe('Member 2')
  })
})

// ── Tests: assertNoModelNamesInPrompt ─────────────────────────────────────────

describe('assertNoModelNamesInPrompt', () => {
  const safeOutputs: PanelMemberOutput[] = [
    { member_index: 0, model_id: 'custom-model-x', provider_family: 'anthropic', status: 'success', answer: 'answer', latency_ms: 100 },
  ]

  it('does not throw for a prompt with no provider names or model ids', () => {
    expect(() =>
      assertNoModelNamesInPrompt('The panel members analyzed the 7th house thoroughly.', safeOutputs),
    ).not.toThrow()
  })

  it('throws when prompt contains "anthropic"', () => {
    expect(() =>
      assertNoModelNamesInPrompt('anthropic model analyzed this', safeOutputs),
    ).toThrow(/Anonymization violation/)
  })

  it('throws when prompt contains "claude" (case-insensitive)', () => {
    expect(() =>
      assertNoModelNamesInPrompt('Claude said the 7th house...', safeOutputs),
    ).toThrow(/Anonymization violation/)
  })

  it('throws when prompt contains "openai"', () => {
    expect(() =>
      assertNoModelNamesInPrompt('openai member contributed this', safeOutputs),
    ).toThrow(/Anonymization violation/)
  })

  it('throws when prompt contains "gpt"', () => {
    expect(() =>
      assertNoModelNamesInPrompt('gpt-4 said something', safeOutputs),
    ).toThrow(/Anonymization violation/)
  })

  it('throws when prompt contains "gemini"', () => {
    expect(() =>
      assertNoModelNamesInPrompt('gemini analyzed the chart', safeOutputs),
    ).toThrow(/Anonymization violation/)
  })

  it('throws when prompt contains "deepseek"', () => {
    expect(() =>
      assertNoModelNamesInPrompt('deepseek processed the query', safeOutputs),
    ).toThrow(/Anonymization violation/)
  })

  it('throws when prompt contains a specific model id from memberOutputs', () => {
    const outputs: PanelMemberOutput[] = [
      { member_index: 0, model_id: 'my-secret-model-v99', provider_family: 'anthropic', status: 'success', answer: 'answer', latency_ms: 100 },
    ]
    expect(() =>
      assertNoModelNamesInPrompt('Response from my-secret-model-v99 here', outputs),
    ).toThrow(/Anonymization violation/)
  })
})

// ── Tests: synthesis result shape ─────────────────────────────────────────────

describe('adjudicate — synthesis result', () => {
  it('returns final_answer, divergence_summary, member_alignment, adjudicator_model_id', async () => {
    mockRunAdapter.mockResolvedValue({ finalText: makeValidAdjudicatorJson(), usage: { inputTokens: 0, outputTokens: 0 }, finishReason: 'stop', intermediate: [] })

    const result = await adjudicate(threeSuccessOutputs, fakeSynthesisRequest, threeMembers)

    expect(result.final_answer).toBe('The 7th house indicates partnerships.')
    expect(result.divergence_summary).toMatchObject({ has_divergence: false, divergence_count: 0 })
    expect(result.adjudicator_model_id).toBe('deepseek-chat')
    expect(typeof result.latency_ms).toBe('number')
  })

  it('handles partial and dissent alignment values', async () => {
    const json = makeValidAdjudicatorJson({
      divergence_summary: { has_divergence: true, divergence_count: 1, summary_text: 'Member 3 interpreted differently.' },
      member_alignment: { 'Member 1': 'aligned', 'Member 2': 'partial', 'Member 3': 'dissent' },
    })
    mockRunAdapter.mockResolvedValue({ finalText: json, usage: { inputTokens: 0, outputTokens: 0 }, finishReason: 'stop', intermediate: [] })

    const result = await adjudicate(threeSuccessOutputs, fakeSynthesisRequest, threeMembers)

    expect(result.member_alignment['Member 2']).toBe('partial')
    expect(result.member_alignment['Member 3']).toBe('dissent')
    expect(result.divergence_summary.has_divergence).toBe(true)
  })
})

// ── Tests: JSON parse fallback ─────────────────────────────────────────────────

describe('adjudicate — JSON parse error fallback', () => {
  it('returns raw text as final_answer when response is not JSON', async () => {
    const rawText = 'The 7th house is about partnerships and balance in life.'
    mockRunAdapter.mockResolvedValue({ finalText: rawText, usage: { inputTokens: 0, outputTokens: 0 }, finishReason: 'stop', intermediate: [] })

    const result = await adjudicate(threeSuccessOutputs, fakeSynthesisRequest, threeMembers)

    expect(result.final_answer).toBe(rawText)
    expect(result.divergence_summary.has_divergence).toBe(false)
    expect(result.divergence_summary.summary_text).toMatch(/parse error/)
    expect(result.member_alignment).toEqual({})
  })

  it('strips markdown fences and parses JSON successfully', async () => {
    const json = makeValidAdjudicatorJson()
    mockRunAdapter.mockResolvedValue({ finalText: `\`\`\`json\n${json}\n\`\`\``, usage: { inputTokens: 0, outputTokens: 0 }, finishReason: 'stop', intermediate: [] })

    const result = await adjudicate(threeSuccessOutputs, fakeSynthesisRequest, threeMembers)

    expect(result.final_answer).toBe('The 7th house indicates partnerships.')
  })
})

// ── Tests: error propagation ───────────────────────────────────────────────────

describe('adjudicate — error propagation', () => {
  it('propagates error when generateText rejects', async () => {
    mockRunAdapter.mockRejectedValue(new Error('LLM API failure'))

    await expect(
      adjudicate(threeSuccessOutputs, fakeSynthesisRequest, threeMembers),
    ).rejects.toThrow('LLM API failure')
  })

  it('throws when fewer than 2 successful members are passed', async () => {
    const oneSuccessOutput: PanelMemberOutput[] = [
      { member_index: 0, model_id: 'claude-sonnet-4-6', provider_family: 'anthropic', status: 'success', answer: 'answer', latency_ms: 100 },
    ]

    await expect(
      adjudicate(oneSuccessOutput, fakeSynthesisRequest, threeMembers),
    ).rejects.toThrow(/≥2 anonymized member outputs/)
  })

  it('throws anonymization violation when loadAdjudicatorPrompt returns a prompt containing "anthropic"', async () => {
    vi.mocked(loadAdjudicatorPrompt).mockReturnValueOnce(
      'Response from anthropic member: some analysis',
    )

    await expect(
      adjudicate(threeSuccessOutputs, fakeSynthesisRequest, threeMembers),
    ).rejects.toThrow(/Anonymization violation/)
  })
})
