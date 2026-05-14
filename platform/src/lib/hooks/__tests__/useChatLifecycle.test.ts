import { describe, it, expect } from 'vitest'
import {
  chatLifecycleReducer,
  INITIAL_SNAPSHOT,
  type ChatLifecycleSnapshot,
  type ChatLifecycleAction,
} from '../useChatLifecycle'
import type { ModelInteraction } from '@/lib/adapters/types'

// ── Helpers ────────────────────────────────────────────────────────────────────

function reduce(
  state: ChatLifecycleSnapshot,
  ...actions: ChatLifecycleAction[]
): ChatLifecycleSnapshot {
  return actions.reduce(chatLifecycleReducer, state)
}

const DUMMY_INTERACTION: ModelInteraction = {
  modelId: 'gemini-2.5-pro',
  provider: 'google',
  intermediate: [],
  finishReason: 'stop',
  usage: {
    inputTokens: 100,
    outputTokens: 50,
    costUsd: 0.002,
    latencyMs: 1200,
  },
  providerMeta: {},
}

// ── RESET ──────────────────────────────────────────────────────────────────────

describe('RESET action', () => {
  it('returns INITIAL_SNAPSHOT from any state', () => {
    const dirty = reduce(
      INITIAL_SNAPSHOT,
      { type: 'STATUS', status: 'composing' },
      { type: 'TEXT_DELTA', text: 'hello' },
    )
    const result = chatLifecycleReducer(dirty, { type: 'RESET' })
    expect(result).toEqual(INITIAL_SNAPSHOT)
  })

  it('idle state remains idle on RESET', () => {
    const result = chatLifecycleReducer(INITIAL_SNAPSHOT, { type: 'RESET' })
    expect(result.state).toBe('idle')
  })
})

// ── STATUS transitions ─────────────────────────────────────────────────────────

describe('STATUS action — state transitions', () => {
  it('idle → queued', () => {
    const result = chatLifecycleReducer(INITIAL_SNAPSHOT, { type: 'STATUS', status: 'queued' })
    expect(result.state).toBe('queued')
  })

  it('queued → planning', () => {
    const s = reduce(INITIAL_SNAPSHOT, { type: 'STATUS', status: 'queued' })
    expect(chatLifecycleReducer(s, { type: 'STATUS', status: 'planning' }).state).toBe('planning')
  })

  it('planning → retrieving', () => {
    const s = reduce(INITIAL_SNAPSHOT, { type: 'STATUS', status: 'planning' })
    expect(chatLifecycleReducer(s, { type: 'STATUS', status: 'retrieving' }).state).toBe('retrieving')
  })

  it('retrieving → reasoning', () => {
    const s = reduce(INITIAL_SNAPSHOT, { type: 'STATUS', status: 'retrieving' })
    expect(chatLifecycleReducer(s, { type: 'STATUS', status: 'reasoning' }).state).toBe('reasoning')
  })

  it('reasoning → tool_calling', () => {
    const s = reduce(INITIAL_SNAPSHOT, { type: 'STATUS', status: 'reasoning' })
    expect(chatLifecycleReducer(s, { type: 'STATUS', status: 'tool_calling' }).state).toBe('tool_calling')
  })

  it('tool_calling → composing', () => {
    const s = reduce(INITIAL_SNAPSHOT, { type: 'STATUS', status: 'tool_calling' })
    expect(chatLifecycleReducer(s, { type: 'STATUS', status: 'composing' }).state).toBe('composing')
  })

  it('composing → complete', () => {
    const s = reduce(INITIAL_SNAPSHOT, { type: 'STATUS', status: 'composing' })
    expect(chatLifecycleReducer(s, { type: 'STATUS', status: 'complete' }).state).toBe('complete')
  })

  it('STATUS does not reset accumulated text', () => {
    const s = reduce(
      INITIAL_SNAPSHOT,
      { type: 'STATUS', status: 'composing' },
      { type: 'TEXT_DELTA', text: 'partial' },
    )
    const result = chatLifecycleReducer(s, { type: 'STATUS', status: 'complete' })
    expect(result.finalText).toBe('partial')
  })

  it('STATUS preserves reasoningText across transition', () => {
    const s = reduce(
      INITIAL_SNAPSHOT,
      { type: 'REASONING_DELTA', text: 'thought' },
    )
    const result = chatLifecycleReducer(s, { type: 'STATUS', status: 'composing' })
    expect(result.reasoningText).toBe('thought')
  })
})

// ── REASONING_DELTA ────────────────────────────────────────────────────────────

describe('REASONING_DELTA action', () => {
  it('appends text to empty reasoningText', () => {
    const result = chatLifecycleReducer(INITIAL_SNAPSHOT, { type: 'REASONING_DELTA', text: 'step 1' })
    expect(result.reasoningText).toBe('step 1')
  })

  it('accumulates multiple reasoning_delta events', () => {
    const result = reduce(
      INITIAL_SNAPSHOT,
      { type: 'REASONING_DELTA', text: 'a' },
      { type: 'REASONING_DELTA', text: 'b' },
      { type: 'REASONING_DELTA', text: 'c' },
    )
    expect(result.reasoningText).toBe('abc')
  })

  it('does not change state', () => {
    const s = reduce(INITIAL_SNAPSHOT, { type: 'STATUS', status: 'reasoning' })
    const result = chatLifecycleReducer(s, { type: 'REASONING_DELTA', text: 'x' })
    expect(result.state).toBe('reasoning')
  })

  it('does not affect finalText', () => {
    const result = chatLifecycleReducer(INITIAL_SNAPSHOT, { type: 'REASONING_DELTA', text: 'x' })
    expect(result.finalText).toBe('')
  })
})

// ── TOOL_CALL / TOOL_RESULT ────────────────────────────────────────────────────

describe('TOOL_CALL + TOOL_RESULT actions', () => {
  it('appends a tool call to empty toolCalls', () => {
    const result = chatLifecycleReducer(INITIAL_SNAPSHOT, {
      type: 'TOOL_CALL', callId: 'c1', name: 'msr_sql', args: { limit: 10 }, ts: 1000,
    })
    expect(result.toolCalls).toHaveLength(1)
    expect(result.toolCalls[0].name).toBe('msr_sql')
    expect(result.toolCalls[0].result).toBeUndefined()
  })

  it('preserves chronological order of tool calls', () => {
    const result = reduce(
      INITIAL_SNAPSHOT,
      { type: 'TOOL_CALL', callId: 'c1', name: 'tool_a', args: {}, ts: 100 },
      { type: 'TOOL_CALL', callId: 'c2', name: 'tool_b', args: {}, ts: 200 },
    )
    expect(result.toolCalls[0].name).toBe('tool_a')
    expect(result.toolCalls[1].name).toBe('tool_b')
  })

  it('TOOL_RESULT attaches result to matching callId', () => {
    const s = chatLifecycleReducer(INITIAL_SNAPSHOT, {
      type: 'TOOL_CALL', callId: 'c1', name: 'vector_search', args: {}, ts: 1000,
    })
    const result = chatLifecycleReducer(s, {
      type: 'TOOL_RESULT', callId: 'c1', result: { rows: 5 },
    })
    expect(result.toolCalls[0].result).toEqual({ rows: 5 })
  })

  it('TOOL_RESULT does not affect other tool calls', () => {
    const s = reduce(
      INITIAL_SNAPSHOT,
      { type: 'TOOL_CALL', callId: 'c1', name: 'tool_a', args: {}, ts: 100 },
      { type: 'TOOL_CALL', callId: 'c2', name: 'tool_b', args: {}, ts: 200 },
    )
    const result = chatLifecycleReducer(s, { type: 'TOOL_RESULT', callId: 'c2', result: 'done' })
    expect(result.toolCalls[0].result).toBeUndefined()
    expect(result.toolCalls[1].result).toBe('done')
  })

  it('TOOL_RESULT with unknown callId leaves toolCalls unchanged', () => {
    const s = chatLifecycleReducer(INITIAL_SNAPSHOT, {
      type: 'TOOL_CALL', callId: 'c1', name: 'msr_sql', args: {}, ts: 1000,
    })
    const result = chatLifecycleReducer(s, { type: 'TOOL_RESULT', callId: 'xx', result: 'x' })
    expect(result.toolCalls[0].result).toBeUndefined()
  })
})

// ── TEXT_DELTA ─────────────────────────────────────────────────────────────────

describe('TEXT_DELTA action', () => {
  it('appends text to empty finalText', () => {
    const result = chatLifecycleReducer(INITIAL_SNAPSHOT, { type: 'TEXT_DELTA', text: 'Hello' })
    expect(result.finalText).toBe('Hello')
  })

  it('accumulates multiple text_delta events', () => {
    const result = reduce(
      INITIAL_SNAPSHOT,
      { type: 'TEXT_DELTA', text: 'Hello' },
      { type: 'TEXT_DELTA', text: ' ' },
      { type: 'TEXT_DELTA', text: 'world' },
    )
    expect(result.finalText).toBe('Hello world')
  })

  it('does not change state', () => {
    const s = reduce(INITIAL_SNAPSHOT, { type: 'STATUS', status: 'composing' })
    const result = chatLifecycleReducer(s, { type: 'TEXT_DELTA', text: 'x' })
    expect(result.state).toBe('composing')
  })

  it('does not affect reasoningText', () => {
    const result = chatLifecycleReducer(INITIAL_SNAPSHOT, { type: 'TEXT_DELTA', text: 'x' })
    expect(result.reasoningText).toBe('')
  })
})

// ── FINISH ─────────────────────────────────────────────────────────────────────

describe('FINISH action', () => {
  it('transitions state to complete', () => {
    const result = chatLifecycleReducer(INITIAL_SNAPSHOT, {
      type: 'FINISH', interaction: DUMMY_INTERACTION,
    })
    expect(result.state).toBe('complete')
  })

  it('populates modelMeta from interaction', () => {
    const result = chatLifecycleReducer(INITIAL_SNAPSHOT, {
      type: 'FINISH', interaction: DUMMY_INTERACTION,
    })
    expect(result.modelMeta).toMatchObject({
      modelId: 'gemini-2.5-pro',
      cost: 0.002,
      latencyMs: 1200,
    })
  })

  it('preserves finalText on finish', () => {
    const s = reduce(
      INITIAL_SNAPSHOT,
      { type: 'TEXT_DELTA', text: 'Full answer here.' },
    )
    const result = chatLifecycleReducer(s, { type: 'FINISH', interaction: DUMMY_INTERACTION })
    expect(result.finalText).toBe('Full answer here.')
  })

  it('preserves reasoningText on finish', () => {
    const s = reduce(
      INITIAL_SNAPSHOT,
      { type: 'REASONING_DELTA', text: 'reasoning content' },
    )
    const result = chatLifecycleReducer(s, { type: 'FINISH', interaction: DUMMY_INTERACTION })
    expect(result.reasoningText).toBe('reasoning content')
  })

  it('preserves toolCalls on finish', () => {
    const s = reduce(
      INITIAL_SNAPSHOT,
      { type: 'TOOL_CALL', callId: 'c1', name: 'msr_sql', args: {}, ts: 1000 },
    )
    const result = chatLifecycleReducer(s, { type: 'FINISH', interaction: DUMMY_INTERACTION })
    expect(result.toolCalls).toHaveLength(1)
  })
})

// ── ERROR ──────────────────────────────────────────────────────────────────────

describe('ERROR action', () => {
  it('transitions state to error', () => {
    const result = chatLifecycleReducer(INITIAL_SNAPSHOT, {
      type: 'ERROR', error: { message: 'Provider timeout', code: 'timeout' },
    })
    expect(result.state).toBe('error')
  })

  it('attaches error details', () => {
    const result = chatLifecycleReducer(INITIAL_SNAPSHOT, {
      type: 'ERROR', error: { message: 'auth_fail' },
    })
    expect(result.error?.message).toBe('auth_fail')
  })

  it('error from mid-stream preserves accumulated text', () => {
    const s = reduce(
      INITIAL_SNAPSHOT,
      { type: 'STATUS', status: 'composing' },
      { type: 'TEXT_DELTA', text: 'partial answer' },
    )
    const result = chatLifecycleReducer(s, { type: 'ERROR', error: { message: 'network' } })
    expect(result.finalText).toBe('partial answer')
    expect(result.state).toBe('error')
  })
})

// ── CANCEL ─────────────────────────────────────────────────────────────────────

describe('CANCEL action', () => {
  it('transitions state to cancelled', () => {
    const s = reduce(INITIAL_SNAPSHOT, { type: 'STATUS', status: 'composing' })
    const result = chatLifecycleReducer(s, { type: 'CANCEL' })
    expect(result.state).toBe('cancelled')
  })

  it('preserves finalText on cancel', () => {
    const s = reduce(
      INITIAL_SNAPSHOT,
      { type: 'TEXT_DELTA', text: 'partial' },
    )
    const result = chatLifecycleReducer(s, { type: 'CANCEL' })
    expect(result.finalText).toBe('partial')
  })
})

// ── Full happy-path sequence ───────────────────────────────────────────────────

describe('Full turn sequence', () => {
  it('queued → planning → retrieving → reasoning → composing → complete', () => {
    const final = reduce(
      INITIAL_SNAPSHOT,
      { type: 'STATUS', status: 'queued' },
      { type: 'STATUS', status: 'planning' },
      { type: 'STATUS', status: 'retrieving' },
      { type: 'STATUS', status: 'reasoning' },
      { type: 'REASONING_DELTA', text: 'Thought 1. ' },
      { type: 'REASONING_DELTA', text: 'Thought 2.' },
      { type: 'STATUS', status: 'composing' },
      { type: 'TEXT_DELTA', text: 'Answer part A. ' },
      { type: 'TEXT_DELTA', text: 'Answer part B.' },
      { type: 'FINISH', interaction: DUMMY_INTERACTION },
    )
    expect(final.state).toBe('complete')
    expect(final.reasoningText).toBe('Thought 1. Thought 2.')
    expect(final.finalText).toBe('Answer part A. Answer part B.')
    expect(final.modelMeta?.modelId).toBe('gemini-2.5-pro')
  })

  it('turn with tool calls: queued → tool_calling → composing → complete', () => {
    const final = reduce(
      INITIAL_SNAPSHOT,
      { type: 'STATUS', status: 'queued' },
      { type: 'STATUS', status: 'tool_calling' },
      { type: 'TOOL_CALL', callId: 'tc1', name: 'msr_sql', args: { q: 'x' }, ts: 1000 },
      { type: 'TOOL_RESULT', callId: 'tc1', result: [{ signal: 'SIG.1' }] },
      { type: 'STATUS', status: 'composing' },
      { type: 'TEXT_DELTA', text: 'Based on signals...' },
      { type: 'FINISH', interaction: DUMMY_INTERACTION },
    )
    expect(final.state).toBe('complete')
    expect(final.toolCalls).toHaveLength(1)
    expect(final.toolCalls[0].result).toEqual([{ signal: 'SIG.1' }])
  })
})

// ── Immutability guard ─────────────────────────────────────────────────────────

describe('Immutability', () => {
  it('TOOL_CALL returns a new array reference', () => {
    const s = INITIAL_SNAPSHOT
    const result = chatLifecycleReducer(s, {
      type: 'TOOL_CALL', callId: 'c1', name: 'n', args: {}, ts: 0,
    })
    expect(result.toolCalls).not.toBe(s.toolCalls)
  })

  it('unknown action returns same state reference', () => {
    const result = chatLifecycleReducer(
      INITIAL_SNAPSHOT,
      // @ts-expect-error testing unknown action type
      { type: 'UNKNOWN' },
    )
    expect(result).toBe(INITIAL_SNAPSHOT)
  })
})
