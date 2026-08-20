/**
 * lane P2-E — synthesis_observation.ts. Proves the wiring is REAL: a fake
 * `ObservatoryDb` captures the exact SQL/params `computeCost` +
 * `persistObservation` (the EXISTING, previously-uncalled machinery) issue,
 * and the identity-absent path is proven to skip rather than fabricate.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

import {
  recordSynthesisTurnObservation,
  buildSynthesisParameters,
  __resetObservabilityWarnLatchForTests,
} from '../synthesis_observation'
import type { TurnMetricsSnapshot } from '../turn_metrics'
import type { ObservatoryDb } from '@/lib/llm/observability/types'

function emptySnapshot(overrides: Partial<TurnMetricsSnapshot> = {}): TurnMetricsSnapshot {
  return {
    ttft_ms: 120,
    event_count: 10,
    events_by_type: { text_delta: 8, usage: 1, message_stop: 1 },
    max_event_gap_ms: 40,
    usage: { input_tokens: 1000, output_tokens: 200, cache_read_tokens: 0, cache_write_tokens: 0, reasoning_tokens: 0 },
    register_lint: { delta_calls: 8, fires: 1, leaks_total: 2 },
    delta_commit_lag_ms: { count: 2, total_ms: 300, max_ms: 200 },
    pass_count: 1,
    ...overrides,
  }
}

function fakeDb(opts: { pricingRows?: unknown[] } = {}): { db: ObservatoryDb; calls: { sql: string; params: unknown[] | undefined }[] } {
  const calls: { sql: string; params: unknown[] | undefined }[] = []
  const db: ObservatoryDb = {
    query: async (sql: string, params?: unknown[]) => {
      calls.push({ sql, params })
      if (sql.includes('FROM llm_pricing_versions')) {
        return { rows: (opts.pricingRows ?? []) as never[], rowCount: (opts.pricingRows ?? []).length }
      }
      if (sql.includes('INSERT INTO llm_usage_events')) {
        return { rows: [{ event_id: 'fake-event-id' }] as never[], rowCount: 1 }
      }
      return { rows: [] as never[], rowCount: 0 }
    },
  }
  return { db, calls }
}

describe('recordSynthesisTurnObservation', () => {
  beforeEach(() => {
    __resetObservabilityWarnLatchForTests()
    vi.restoreAllMocks()
  })

  it('SKIPS the write and warns once when identity is absent (never fabricates conversation_id/user_id)', async () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const { db, calls } = fakeDb()

    await recordSynthesisTurnObservation({
      identity: undefined,
      stackId: 'anthropic',
      modelId: 'claude-x',
      startedAt: new Date(),
      finishedAt: new Date(),
      status: 'success',
      snapshot: emptySnapshot(),
      db,
    })
    await recordSynthesisTurnObservation({
      identity: undefined,
      stackId: 'anthropic',
      modelId: 'claude-x',
      startedAt: new Date(),
      finishedAt: new Date(),
      status: 'success',
      snapshot: emptySnapshot(),
      db,
    })

    expect(calls.length).toBe(0) // no DB call at all — an honest skip, not a bad write
    expect(warn).toHaveBeenCalledTimes(1) // logs once, not once per turn
  })

  it('writes a real INSERT with the mapped provider name and channel default when identity IS present', async () => {
    const { db, calls } = fakeDb({ pricingRows: [] }) // no pricing → honest null cost, not a crash

    await recordSynthesisTurnObservation({
      identity: { turnId: 'turn-1', conversationId: 'conv-1', userId: 'user-1' },
      stackId: 'google', // must translate to 'gemini' for the CHECK constraint
      modelId: 'gemini-x',
      startedAt: new Date('2026-08-19T00:00:00.000Z'),
      finishedAt: new Date('2026-08-19T00:00:02.000Z'),
      status: 'success',
      snapshot: emptySnapshot(),
      db,
    })

    const insertCall = calls.find((c) => c.sql.includes('INSERT INTO llm_usage_events'))
    expect(insertCall).toBeDefined()
    const params = insertCall!.params!
    // Column order from persist.ts's INSERT_SQL: conversation_id, conversation_name,
    // prompt_id, parent_prompt_id, user_id, provider, model, pipeline_stage, ...
    expect(params[0]).toBe('conv-1') // conversation_id
    expect(params[2]).toBe('turn-1') // prompt_id
    expect(params[4]).toBe('user-1') // user_id
    expect(params[5]).toBe('gemini') // provider — translated, not the raw StackId 'google'
    expect(params[6]).toBe('gemini-x') // model
    expect(params[7]).toBe('synthesize') // pipeline_stage
    expect(params[params.length - 1]).toBe('web') // channel — default per this lane's design
  })

  it('degrades cost to null (never a fabricated number) when no pricing row matches', async () => {
    const { db, calls } = fakeDb({ pricingRows: [] })
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    await recordSynthesisTurnObservation({
      identity: { turnId: 't', conversationId: 'c', userId: 'u' },
      stackId: 'anthropic',
      modelId: 'unpriced-model',
      startedAt: new Date(),
      finishedAt: new Date(),
      status: 'success',
      snapshot: emptySnapshot(),
      db,
    })

    const insertCall = calls.find((c) => c.sql.includes('INSERT INTO llm_usage_events'))
    const params = insertCall!.params!
    // computed_cost_usd is the 18th positional param (index 17) in persist.ts's INSERT_SQL.
    expect(params[17]).toBeNull()
    // PricingNotFoundError is an EXPECTED gap, not logged as an error.
    expect(errorSpy).not.toHaveBeenCalled()
  })

  it('never throws when the DB itself fails (fire-and-forget discipline)', async () => {
    const db: ObservatoryDb = {
      query: async () => {
        throw new Error('connection refused')
      },
    }
    vi.spyOn(console, 'error').mockImplementation(() => {})

    await expect(
      recordSynthesisTurnObservation({
        identity: { turnId: 't', conversationId: 'c', userId: 'u' },
        stackId: 'anthropic',
        modelId: 'claude-x',
        startedAt: new Date(),
        finishedAt: new Date(),
        status: 'success',
        snapshot: emptySnapshot(),
        db,
      }),
    ).resolves.toBeUndefined()
  })
})

describe('buildSynthesisParameters', () => {
  it('carries every metric that has no dedicated llm_usage_events column', () => {
    const params = buildSynthesisParameters(emptySnapshot())
    expect(params.ttft_ms).toBe(120)
    expect(params.max_event_gap_ms).toBe(40)
    expect(params.register_lint).toEqual({ delta_calls: 8, fires: 1, leaks_total: 2 })
    expect(params.delta_commit_lag_ms).toEqual({ count: 2, total_ms: 300, max_ms: 200 })
    expect(params.pass_count).toBe(1)
  })
})
