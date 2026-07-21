import { describe, it, expect, vi, beforeEach } from 'vitest'

// ── Module mocks (must be before any imports) ─────────────────────────────────
vi.mock('server-only', () => ({}))

const mockRunAdapter = vi.fn()
vi.mock('@/lib/adapters', () => ({
  runAdapter: (...args: unknown[]) => mockRunAdapter(...args),
}))

vi.mock('@/lib/config/index', () => ({
  getFlag: vi.fn(),
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
  loadAdjudicatorPrompt: vi.fn(() => 'test adjudicator prompt'),
}))

const mockConcurrentRetry = vi.fn()
vi.mock('../../panel/concurrent_retry', () => ({
  concurrentRetry: (...args: unknown[]) => mockConcurrentRetry(...args),
}))

// ── Imports (after mocks) ─────────────────────────────────────────────────────
import { runPanelMembers, PanelDegradedError } from '../../panel/member_runner'
import { getFlag } from '@/lib/config/index'
import { telemetry } from '@/lib/telemetry/index'
import type { PanelMemberConfig } from '../../panel/types'
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

const threeMembers: PanelMemberConfig[] = [
  { provider_family: 'anthropic', model_id: 'claude-sonnet-4-6', prompt_variant_tag: 'panel_member_v1' },
  { provider_family: 'openai',    model_id: 'gpt-4.1',            prompt_variant_tag: 'panel_member_v1' },
  { provider_family: 'google',    model_id: 'gemini-2.5-pro',     prompt_variant_tag: 'panel_member_v1' },
]

const mockGetFlag = vi.mocked(getFlag)

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Make concurrentRetry immediately execute the factory it receives. */
function letConcurrentRetryExecute() {
  mockConcurrentRetry.mockImplementation(
    (factory: (signal: AbortSignal) => Promise<unknown>) =>
      factory(new AbortController().signal),
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('runPanelMembers — happy path', () => {
  it('returns member_outputs with status success for all 3 members', async () => {
    letConcurrentRetryExecute()
    mockRunAdapter.mockResolvedValue({ finalText: 'member answer', usage: { inputTokens: 0, outputTokens: 0 }, finishReason: 'stop', intermediate: [] })
    mockGetFlag.mockReturnValue(false)

    const { member_outputs, degrade_notice } = await runPanelMembers(
      fakeSynthesisRequest,
      threeMembers,
    )

    expect(member_outputs).toHaveLength(3)
    for (const o of member_outputs) {
      expect(o.status).toBe('success')
      expect(o.answer).toBe('member answer')
    }
    expect(degrade_notice).toBeUndefined()
  })

  it('attaches correct provider_family and model_id to each output', async () => {
    letConcurrentRetryExecute()
    mockRunAdapter.mockResolvedValue({ finalText: 'answer', usage: { inputTokens: 0, outputTokens: 0 }, finishReason: 'stop', intermediate: [] })
    mockGetFlag.mockReturnValue(false)

    const { member_outputs } = await runPanelMembers(fakeSynthesisRequest, threeMembers)

    expect(member_outputs[0].provider_family).toBe('anthropic')
    expect(member_outputs[0].model_id).toBe('claude-sonnet-4-6')
    expect(member_outputs[1].provider_family).toBe('openai')
    expect(member_outputs[2].provider_family).toBe('google')
  })

  it('records telemetry for members_attempted and members_succeeded', async () => {
    letConcurrentRetryExecute()
    mockRunAdapter.mockResolvedValue({ finalText: 'answer', usage: { inputTokens: 0, outputTokens: 0 }, finishReason: 'stop', intermediate: [] })
    mockGetFlag.mockReturnValue(false)

    await runPanelMembers(fakeSynthesisRequest, threeMembers)

    expect(vi.mocked(telemetry.recordMetric)).toHaveBeenCalledWith('panel', 'members_attempted', 3)
    expect(vi.mocked(telemetry.recordMetric)).toHaveBeenCalledWith('panel', 'members_succeeded', 3)
  })
})

describe('runPanelMembers — one member fails, PANEL_DEGRADE_2_OF_3=false', () => {
  it('throws PanelDegradedError when degrade flag is false', async () => {
    mockGetFlag.mockReturnValue(false)

    let call = 0
    mockConcurrentRetry.mockImplementation(
      (factory: (signal: AbortSignal) => Promise<unknown>) => {
        call++
        if (call === 2) return Promise.reject(new Error('member 1 LLM error'))
        return factory(new AbortController().signal)
      },
    )
    mockRunAdapter.mockResolvedValue({ finalText: 'answer', usage: { inputTokens: 0, outputTokens: 0 }, finishReason: 'stop', intermediate: [] })

    await expect(
      runPanelMembers(fakeSynthesisRequest, threeMembers),
    ).rejects.toBeInstanceOf(PanelDegradedError)
  })

  it('PanelDegradedError carries the failed member index', async () => {
    mockGetFlag.mockReturnValue(false)

    let call = 0
    mockConcurrentRetry.mockImplementation(
      (factory: (signal: AbortSignal) => Promise<unknown>) => {
        call++
        if (call === 2) return Promise.reject(new Error('member 1 down'))
        return factory(new AbortController().signal)
      },
    )
    mockRunAdapter.mockResolvedValue({ finalText: 'answer', usage: { inputTokens: 0, outputTokens: 0 }, finishReason: 'stop', intermediate: [] })

    const err = await runPanelMembers(fakeSynthesisRequest, threeMembers).catch(e => e)
    expect(err).toBeInstanceOf(PanelDegradedError)
    expect((err as PanelDegradedError).failed_index).toBe(1)
  })
})

describe('runPanelMembers — one member fails, PANEL_DEGRADE_2_OF_3=true', () => {
  it('proceeds and returns degrade_notice with surviving_members=2', async () => {
    mockGetFlag.mockReturnValue(true)

    let call = 0
    mockConcurrentRetry.mockImplementation(
      (factory: (signal: AbortSignal) => Promise<unknown>) => {
        call++
        if (call === 3) return Promise.reject(new Error('member 2 down'))
        return factory(new AbortController().signal)
      },
    )
    mockRunAdapter.mockResolvedValue({ finalText: 'answer', usage: { inputTokens: 0, outputTokens: 0 }, finishReason: 'stop', intermediate: [] })

    const { member_outputs, degrade_notice } = await runPanelMembers(
      fakeSynthesisRequest,
      threeMembers,
    )

    expect(degrade_notice).toBeDefined()
    expect(degrade_notice!.surviving_members).toBe(2)
    expect(member_outputs.filter(o => o.status === 'success')).toHaveLength(2)
    expect(member_outputs.filter(o => o.status === 'failed')).toHaveLength(1)
  })

  it('records degrade_engaged telemetry metric', async () => {
    mockGetFlag.mockReturnValue(true)

    let call = 0
    mockConcurrentRetry.mockImplementation(
      (factory: (signal: AbortSignal) => Promise<unknown>) => {
        call++
        if (call === 1) return Promise.reject(new Error('member 0 down'))
        return factory(new AbortController().signal)
      },
    )
    mockRunAdapter.mockResolvedValue({ finalText: 'answer', usage: { inputTokens: 0, outputTokens: 0 }, finishReason: 'stop', intermediate: [] })

    await runPanelMembers(fakeSynthesisRequest, threeMembers)

    expect(vi.mocked(telemetry.recordMetric)).toHaveBeenCalledWith('panel', 'degrade_engaged', 1)
  })
})

describe('runPanelMembers — all members fail', () => {
  it('throws PanelDegradedError regardless of degrade flag (degrade=false)', async () => {
    mockGetFlag.mockReturnValue(false)
    mockConcurrentRetry.mockRejectedValue(new Error('all down'))

    await expect(
      runPanelMembers(fakeSynthesisRequest, threeMembers),
    ).rejects.toBeInstanceOf(PanelDegradedError)
  })

  it('throws PanelDegradedError when degrade=true but only 1 survives', async () => {
    mockGetFlag.mockReturnValue(true)

    let call = 0
    mockConcurrentRetry.mockImplementation(
      (factory: (signal: AbortSignal) => Promise<unknown>) => {
        call++
        if (call !== 1) return Promise.reject(new Error(`member ${call - 1} down`))
        return factory(new AbortController().signal)
      },
    )
    mockRunAdapter.mockResolvedValue({ finalText: 'answer', usage: { inputTokens: 0, outputTokens: 0 }, finishReason: 'stop', intermediate: [] })

    await expect(
      runPanelMembers(fakeSynthesisRequest, threeMembers),
    ).rejects.toBeInstanceOf(PanelDegradedError)
  })

  it('throws when degrade=true but all 3 fail (0 survive)', async () => {
    mockGetFlag.mockReturnValue(true)
    mockConcurrentRetry.mockRejectedValue(new Error('total failure'))

    await expect(
      runPanelMembers(fakeSynthesisRequest, threeMembers),
    ).rejects.toBeInstanceOf(PanelDegradedError)
  })
})

describe('runPanelMembers — concurrent retry wiring', () => {
  it('passes RETRY_ATTEMPTS=3 to concurrentRetry for each member', async () => {
    letConcurrentRetryExecute()
    mockRunAdapter.mockResolvedValue({ finalText: 'answer', usage: { inputTokens: 0, outputTokens: 0 }, finishReason: 'stop', intermediate: [] })
    mockGetFlag.mockReturnValue(false)

    await runPanelMembers(fakeSynthesisRequest, threeMembers)

    // concurrentRetry should be called once per member (3 members)
    expect(mockConcurrentRetry).toHaveBeenCalledTimes(3)
    // Each call should have maxAttempts=3 as second arg
    for (const call of mockConcurrentRetry.mock.calls) {
      expect(call[1]).toBe(3)
    }
  })
})

describe('runPanelMembers — timeout', () => {
  it('treats a member as failed when it exceeds MEMBER_TIMEOUT_MS', async () => {
    mockGetFlag.mockReturnValue(true)

    // concurrentRetry transparently executes the factory.
    // The factory races generateText against a timeout.
    // We simulate timeout by making generateText never resolve.
    vi.useFakeTimers()

    mockConcurrentRetry.mockImplementation(
      async (factory: (signal: AbortSignal) => Promise<unknown>) => {
        return factory(new AbortController().signal)
      },
    )

    // Member 0: times out (generateText never resolves for first call)
    // Members 1 & 2: succeed immediately
    let memberCallCount = 0
    mockRunAdapter.mockImplementation(() => {
      memberCallCount++
      if (memberCallCount === 1) {
        // Never resolves — simulate timeout
        return new Promise(() => {})
      }
      return Promise.resolve({ finalText: 'answer', usage: { inputTokens: 0, outputTokens: 0 }, finishReason: 'stop', intermediate: [] })
    })

    const runPromise = runPanelMembers(fakeSynthesisRequest, threeMembers)

    // Advance timers past MEMBER_TIMEOUT_MS (30_000 ms)
    await vi.advanceTimersByTimeAsync(31_000)

    const { member_outputs, degrade_notice } = await runPromise

    expect(member_outputs[0].status).toBe('failed')
    expect(member_outputs[0].error).toMatch(/timed out/)
    expect(degrade_notice).toBeDefined()
    expect(degrade_notice!.surviving_members).toBe(2)

    vi.useRealTimers()
  })
})
