/**
 * prashna_ask_synthesis.test.ts — W6.2 fix-cycle.
 *
 * Covers `synthesizeReading`: the single, non-agentic LLM call that turns
 * prashna_ask's already-gathered floor evidence into an acharya-grade reading.
 * Never throws on failure (DB lookup, model resolution, the model call
 * itself, or an empty response) — every failure mode resolves to
 * `{reading: null, judgment_flags: [...]}` so the caller can still return the
 * honest evidence bundle.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => mockQuery(...args) }))

const mockRunAdapter = vi.fn()
vi.mock('@/lib/adapters/run_adapter', () => ({ runAdapter: (...args: unknown[]) => mockRunAdapter(...args) }))

const mockGetEffectiveModel = vi.fn()
vi.mock('@/lib/models/runtime_config', () => ({ getEffectiveModel: (...args: unknown[]) => mockGetEffectiveModel(...args) }))
vi.mock('@/lib/models/registry', () => ({ DEFAULT_STACK_ID: 'anthropic' }))

import { synthesizeReading, type SynthesizeReadingInput } from '../prashna_ask_synthesis'

const CHART_ROW = {
  id: '482012f1-710e-4a25-994a-93821f5871aa',
  name: 'Test Native',
  birth_date: '1984-02-05',
  birth_time: '10:43',
  birth_place: 'Bhubaneswar, Odisha, India',
}

function baseInput(overrides: Partial<SynthesizeReadingInput> = {}): SynthesizeReadingInput {
  return {
    chartId: CHART_ROW.id,
    question: 'What does my current dasha period suggest about career timing?',
    queryClass: 'predictive',
    queryIntentSummary: 'Career timing via current dasha',
    evidence: [
      { tool_name: 'query_dasha_periods', bundle: { results: [{ lord_graha: 'Mercury' }] } },
    ],
    unresolvedTools: [],
    emptyResultTools: [],
    strippedLeakedCapabilities: [],
    capTripped: null,
    ...overrides,
  }
}

beforeEach(() => {
  mockQuery.mockReset()
  mockRunAdapter.mockReset()
  mockGetEffectiveModel.mockReset()
  mockQuery.mockResolvedValue({ rows: [CHART_ROW] })
  mockGetEffectiveModel.mockResolvedValue('claude-sonnet-test')
  mockRunAdapter.mockResolvedValue({
    modelId: 'claude-sonnet-test',
    provider: 'anthropic',
    intermediate: [],
    finalText: 'Your Mercury-Jupiter period favors steady career growth.',
    finishReason: 'stop',
    usage: { inputTokens: 100, outputTokens: 50, costUsd: 0, latencyMs: 5 },
    providerMeta: {},
  })
})

describe('synthesizeReading — happy path', () => {
  it('returns a reading built from a single non-agentic runAdapter call', async () => {
    const result = await synthesizeReading(baseInput())
    expect(result.reading).toBe('Your Mercury-Jupiter period favors steady career growth.')
    expect(result.model_id).toBe('claude-sonnet-test')
    expect(result.judgment_flags).toEqual([])
    expect(mockRunAdapter).toHaveBeenCalledTimes(1)
  })

  it('does NOT pass a tools array — this is a non-agentic, single-shot call', async () => {
    await synthesizeReading(baseInput())
    const req = mockRunAdapter.mock.calls[0][0] as { tools?: unknown }
    expect(req.tools).toBeUndefined()
  })

  it('the system prompt overrides the base "call tools" instruction for this tool-less call', async () => {
    await synthesizeReading(baseInput())
    const req = mockRunAdapter.mock.calls[0][0] as { systemPrompt: string }
    expect(req.systemPrompt).toMatch(/do not attempt to call/i)
    expect(req.systemPrompt).toMatch(/acharya/i)
  })

  it('includes the gathered evidence in the user message', async () => {
    await synthesizeReading(baseInput())
    const req = mockRunAdapter.mock.calls[0][0] as { messages: Array<{ content: string }> }
    expect(req.messages[0].content).toContain('query_dasha_periods')
    expect(req.messages[0].content).toContain('Mercury')
  })

  it('discloses evidence gaps (unresolved/empty/leaked/cap) in the prompt so the model does not fabricate over them', async () => {
    await synthesizeReading(
      baseInput({
        unresolvedTools: ['pattern_register'],
        emptyResultTools: ['chart_facts_query'],
        strippedLeakedCapabilities: ['marsys://tool/L5/lel_query'],
        capTripped: 'call_count_cap',
      }),
    )
    const req = mockRunAdapter.mock.calls[0][0] as { messages: Array<{ content: string }> }
    const content = req.messages[0].content
    expect(content).toContain('pattern_register')
    expect(content).toContain('unresolved tool name')
    expect(content).toContain('chart_facts_query')
    expect(content).toContain('zero rows')
    expect(content).toContain('marsys://tool/L5/lel_query')
    expect(content).toContain('NO-LEAKAGE')
    expect(content).toContain('call_count_cap')
  })
})

describe('synthesizeReading — never throws, degrades honestly', () => {
  it('resolves reading:null with a flag when the chart context lookup fails', async () => {
    mockQuery.mockRejectedValue(new Error('DB unreachable'))
    const result = await synthesizeReading(baseInput())
    expect(result.reading).toBeNull()
    expect(result.judgment_flags).toContain('synthesis_skipped_chart_context_unresolved')
    expect(mockRunAdapter).not.toHaveBeenCalled()
  })

  it('resolves reading:null with a flag when the chart row does not exist', async () => {
    mockQuery.mockResolvedValue({ rows: [] })
    const result = await synthesizeReading(baseInput())
    expect(result.reading).toBeNull()
    expect(result.judgment_flags).toContain('synthesis_skipped_chart_context_unresolved')
  })

  it('resolves reading:null with a flag when model resolution fails', async () => {
    mockGetEffectiveModel.mockRejectedValue(new Error('no model configured'))
    const result = await synthesizeReading(baseInput())
    expect(result.reading).toBeNull()
    expect(result.judgment_flags).toContain('synthesis_skipped_model_unresolved')
  })

  it('resolves reading:null with a flag when the model call itself throws', async () => {
    mockRunAdapter.mockRejectedValue(new Error('upstream 500'))
    const result = await synthesizeReading(baseInput())
    expect(result.reading).toBeNull()
    expect(result.judgment_flags).toContain('synthesis_call_failed')
  })

  it('resolves reading:null with a flag when the model returns empty/whitespace text', async () => {
    mockRunAdapter.mockResolvedValue({
      modelId: 'claude-sonnet-test',
      provider: 'anthropic',
      intermediate: [],
      finalText: '   ',
      finishReason: 'stop',
      usage: { inputTokens: 10, outputTokens: 0, costUsd: 0, latencyMs: 1 },
      providerMeta: {},
    })
    const result = await synthesizeReading(baseInput())
    expect(result.reading).toBeNull()
    expect(result.judgment_flags).toContain('synthesis_returned_empty')
  })

  it('handles an empty evidence array without crashing', async () => {
    const result = await synthesizeReading(baseInput({ evidence: [] }))
    expect(result.reading).not.toBeNull()
    const req = mockRunAdapter.mock.calls[0][0] as { messages: Array<{ content: string }> }
    expect(req.messages[0].content).toContain('no evidence was gathered')
  })

  it('truncates an oversized evidence item and discloses it via judgment_flags (code-quality follow-up)', async () => {
    // A single result field padded well past the 8,000-char cap — reproduces the
    // real live case (an unfiltered chart_facts_query-class call returned 80KB+).
    const hugeResult = { note: 'x'.repeat(20_000) }
    const result = await synthesizeReading(
      baseInput({ evidence: [{ tool_name: 'chart_facts_query', bundle: { results: [hugeResult] } }] }),
    )
    expect(result.judgment_flags).toContain('synthesis_evidence_truncated')

    const req = mockRunAdapter.mock.calls[0][0] as { messages: Array<{ content: string }> }
    const content = req.messages[0].content
    expect(content).toContain('truncated="true"')
    expect(content).toContain('TRUNCATED')
    // The prompt itself must not balloon to the full 20KB+ payload.
    expect(content.length).toBeLessThan(15_000)
  })

  it('does not flag truncation when every evidence item is under the size cap', async () => {
    const result = await synthesizeReading(baseInput())
    expect(result.judgment_flags).not.toContain('synthesis_evidence_truncated')
  })
})
