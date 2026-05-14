import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

// Mock runAdapter so summarizeHistory never makes a real LLM call.
const mockRunAdapter = vi.fn()
vi.mock('@/lib/adapters', () => ({
  runAdapter: (...args: unknown[]) => mockRunAdapter(...args),
}))

// Mock server-side DB/observability writes used inside summarizeHistory.
vi.mock('@/lib/db/monitoring-write', () => ({
  writeLlmCallLog: vi.fn().mockResolvedValue(undefined),
  resolveProvider: vi.fn(() => 'gemini'),
}))
vi.mock('@/lib/llm/observability', () => ({
  persistObservation: vi.fn().mockResolvedValue(undefined),
  computeCost: vi.fn().mockResolvedValue(null),
}))
vi.mock('@/lib/storage', () => ({
  getStorageClient: vi.fn(() => ({})),
}))

vi.mock('@/lib/models/resolver', () => ({
  resolveModel: (id: string) => ({ __mocked_model_id: id }),
}))

// Import AFTER the mocks are registered.
import { buildPlannerContext } from '@/lib/pipeline/planner_context_builder'

// Current implementation constants (from planner_context_builder.ts):
//   MAX_TOKENS_PER_TURN    = 1000  (4000 chars)
//   HISTORY_BUDGET_TOKENS  = 2000
//   SUMMARY_TARGET_TOKENS  = 512   (2048 chars)
const MAX_TOKENS_PER_TURN = 1000
const HISTORY_BUDGET_TOKENS = 2000
const SUMMARY_TARGET_CHARS = 512 * 4  // 2048

const WORKER = 'mock-worker'

beforeEach(() => {
  mockRunAdapter.mockReset()
})

describe('buildPlannerContext — history window', () => {
  it('empty history → history_turns = [], history_was_summarized = false', async () => {
    const ctx = await buildPlannerContext('What does Saturn signify here?', [], WORKER)
    expect(ctx.history_turns).toEqual([])
    expect(ctx.history_was_summarized).toBe(false)
    expect(ctx.total_estimated_tokens).toBe(Math.ceil('What does Saturn signify here?'.length / 4))
    expect(mockRunAdapter).not.toHaveBeenCalled()
  })

  it('2 short turns → pass-through unchanged, no summarization', async () => {
    const history = [
      { role: 'user',      content: 'hello' },
      { role: 'assistant', content: 'hi, how can I help?' },
    ]
    const ctx = await buildPlannerContext('next query', history, WORKER)
    expect(ctx.history_was_summarized).toBe(false)
    expect(ctx.history_turns).toEqual([
      { role: 'user',      content: 'hello' },
      { role: 'assistant', content: 'hi, how can I help?' },
    ])
    expect(mockRunAdapter).not.toHaveBeenCalled()
  })

  it('3+ turns → only the last 2 are included', async () => {
    const history = [
      { role: 'user',      content: 'first turn — ignored'        },
      { role: 'assistant', content: 'second turn — also ignored'  },
      { role: 'user',      content: 'third turn — kept'           },
      { role: 'assistant', content: 'fourth turn — also kept'     },
    ]
    const ctx = await buildPlannerContext('q', history, WORKER)
    expect(ctx.history_was_summarized).toBe(false)
    expect(ctx.history_turns).toHaveLength(2)
    expect(ctx.history_turns[0].content).toBe('third turn — kept')
    expect(ctx.history_turns[1].content).toBe('fourth turn — also kept')
    expect(mockRunAdapter).not.toHaveBeenCalled()
  })

  it(`single turn > ${MAX_TOKENS_PER_TURN} tokens → truncated to ${MAX_TOKENS_PER_TURN} tokens`, async () => {
    // 6000 chars ≈ 1500 tokens — over the 1000-token per-turn cap.
    // Combined (1500) still ≤ 2000 budget so summarization does NOT trigger.
    const longContent = 'x'.repeat(6000)
    const ctx = await buildPlannerContext('q', [
      { role: 'user', content: longContent },
    ], WORKER)
    expect(ctx.history_was_summarized).toBe(false)
    expect(ctx.history_turns).toHaveLength(1)
    expect(ctx.history_turns[0].content.length).toBe(MAX_TOKENS_PER_TURN * 4)
    expect(Math.ceil(ctx.history_turns[0].content.length / 4)).toBe(MAX_TOKENS_PER_TURN)
    expect(mockRunAdapter).not.toHaveBeenCalled()
  })

  it(`combined raw history > ${HISTORY_BUDGET_TOKENS} tokens → summarized via worker model`, async () => {
    // Two turns each at ~3000 tokens → combined ≈ 6000 tokens (> 2000 budget).
    const longA = 'a'.repeat(12000)  // ~3000 tokens
    const longB = 'b'.repeat(12000)  // ~3000 tokens

    const SUMMARY = 'condensed dialogue summary preserving Saturn-career context.'
    mockRunAdapter.mockResolvedValueOnce({
      finalText: SUMMARY,
      usage: { inputTokens: 100, outputTokens: 20 },
      finishReason: 'stop',
      intermediate: [],
    })

    const ctx = await buildPlannerContext('next query', [
      { role: 'user',      content: longA },
      { role: 'assistant', content: longB },
    ], WORKER)

    expect(ctx.history_was_summarized).toBe(true)
    expect(ctx.history_turns).toHaveLength(1)
    expect(ctx.history_turns[0].role).toBe('user')
    expect(ctx.history_turns[0].content).toContain('condensed dialogue summary')
    // Summary truncated to SUMMARY_TARGET_TOKENS (512 tokens = 2048 chars).
    expect(ctx.history_turns[0].content.length).toBeLessThanOrEqual(SUMMARY_TARGET_CHARS)
    expect(mockRunAdapter).toHaveBeenCalledTimes(1)
    // total_estimated_tokens = query_tokens + summary_tokens.
    const expectedTotal =
      Math.ceil('next query'.length / 4) +
      Math.ceil(ctx.history_turns[0].content.length / 4)
    expect(ctx.total_estimated_tokens).toBe(expectedTotal)
  })

  it('summary that exceeds SUMMARY_TARGET_TOKENS is truncated', async () => {
    // Worker returns a very long summary; builder must clamp to 512 tokens (2048 chars).
    mockRunAdapter.mockResolvedValueOnce({
      finalText: 's'.repeat(10000),  // ~2500 tokens — well over 512
      usage: { inputTokens: 100, outputTokens: 2500 },
      finishReason: 'stop',
      intermediate: [],
    })

    const ctx = await buildPlannerContext('q', [
      { role: 'user',      content: 'a'.repeat(12000) },
      { role: 'assistant', content: 'b'.repeat(12000) },
    ], WORKER)

    expect(ctx.history_was_summarized).toBe(true)
    expect(ctx.history_turns[0].content.length).toBeLessThanOrEqual(SUMMARY_TARGET_CHARS)
  })
})
