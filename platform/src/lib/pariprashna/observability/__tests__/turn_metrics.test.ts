/**
 * lane P2-E — TurnMetricsCollector. Every assertion here is a real,
 * demonstrated-can-fail computation over injected timestamps/events, not a
 * stub returning a constant (CLAUDE.md §N.8).
 */
import { describe, it, expect } from 'vitest'

import { TurnMetricsCollector } from '../turn_metrics'
import type { ChatEvent } from '@/lib/providers/types'

describe('TurnMetricsCollector', () => {
  it('reports ttft_ms as null when no event has arrived', () => {
    const m = new TurnMetricsCollector(1_000)
    expect(m.snapshot().ttft_ms).toBeNull()
    expect(m.snapshot().max_event_gap_ms).toBeNull()
  })

  it('computes TTFT from the first event, not a later one', () => {
    const m = new TurnMetricsCollector(1_000)
    m.recordEvent({ type: 'text_delta', text: 'a' }, 1_250)
    m.recordEvent({ type: 'text_delta', text: 'b' }, 1_400)
    expect(m.snapshot().ttft_ms).toBe(250)
  })

  it('computes the MAX gap between consecutive events, not the average or the last', () => {
    const m = new TurnMetricsCollector(0)
    m.recordEvent({ type: 'text_delta', text: 'a' }, 100) // ttft
    m.recordEvent({ type: 'text_delta', text: 'b' }, 150) // gap 50
    m.recordEvent({ type: 'text_delta', text: 'c' }, 400) // gap 250 <- max
    m.recordEvent({ type: 'text_delta', text: 'd' }, 420) // gap 20
    expect(m.snapshot().max_event_gap_ms).toBe(250)
  })

  it('counts events by type', () => {
    const m = new TurnMetricsCollector(0)
    m.recordEvent({ type: 'text_delta', text: 'a' }, 1)
    m.recordEvent({ type: 'text_delta', text: 'b' }, 2)
    m.recordEvent({ type: 'tool_use_start', id: 't1', name: 'x' }, 3)
    const snap = m.snapshot()
    expect(snap.event_count).toBe(3)
    expect(snap.events_by_type).toEqual({ text_delta: 2, tool_use_start: 1 })
  })

  it('accumulates usage across multiple usage events (multi-pass agentic loop)', () => {
    const m = new TurnMetricsCollector(0)
    const u1: ChatEvent = { type: 'usage', inputTokens: 100, outputTokens: 20, cacheReadTokens: 5 }
    const u2: ChatEvent = { type: 'usage', inputTokens: 40, outputTokens: 10, cacheCreationTokens: 3 }
    m.recordEvent(u1, 1)
    m.recordEvent(u2, 2)
    const usage = m.snapshot().usage
    expect(usage.input_tokens).toBe(140)
    expect(usage.output_tokens).toBe(30)
    expect(usage.cache_read_tokens).toBe(5)
    expect(usage.cache_write_tokens).toBe(3)
    expect(usage.reasoning_tokens).toBe(0)
  })

  it('does not fabricate cache/reasoning tokens a usage event never carried', () => {
    const m = new TurnMetricsCollector(0)
    m.recordEvent({ type: 'usage', inputTokens: 10, outputTokens: 2 }, 1)
    const usage = m.snapshot().usage
    expect(usage.cache_read_tokens).toBe(0)
    expect(usage.cache_write_tokens).toBe(0)
  })

  it('register-lint: only calls with leakCount > 0 count as fires', () => {
    const m = new TurnMetricsCollector(0)
    m.recordRegisterLint(0)
    m.recordRegisterLint(2)
    m.recordRegisterLint(0)
    m.recordRegisterLint(1)
    const rl = m.snapshot().register_lint
    expect(rl.delta_calls).toBe(4)
    expect(rl.fires).toBe(2)
    expect(rl.leaks_total).toBe(3)
  })

  it('delta-commit lag: tracks count/total/max across multiple blocks', () => {
    const m = new TurnMetricsCollector(0)
    m.recordDeltaCommitLag(100)
    m.recordDeltaCommitLag(400)
    m.recordDeltaCommitLag(50)
    const lag = m.snapshot().delta_commit_lag_ms
    expect(lag.count).toBe(3)
    expect(lag.total_ms).toBe(550)
    expect(lag.max_ms).toBe(400)
  })

  it('delta-commit lag: rejects negative/non-finite values rather than corrupting the aggregate', () => {
    const m = new TurnMetricsCollector(0)
    m.recordDeltaCommitLag(-5)
    m.recordDeltaCommitLag(Number.NaN)
    m.recordDeltaCommitLag(30)
    const lag = m.snapshot().delta_commit_lag_ms
    expect(lag.count).toBe(1)
    expect(lag.total_ms).toBe(30)
  })

  it('pass_count starts at 1 and increments only on recordPass()', () => {
    const m = new TurnMetricsCollector(0)
    expect(m.snapshot().pass_count).toBe(1)
    m.recordPass()
    m.recordPass()
    expect(m.snapshot().pass_count).toBe(3)
  })
})
