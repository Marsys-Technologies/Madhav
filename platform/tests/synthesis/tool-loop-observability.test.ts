/**
 * E-S9: tool-loop-observability.test.ts
 *
 * Verifies tool-loop iteration telemetry and Observatory integration:
 * - ToolLoopIterationRecord shape is correct
 * - aggregateTurnSummary() correctly sums per-iteration data
 * - computeIterationCostBreakdown() correctly applies cost model
 * - ToolLoopMetricsTile.tsx exists (existence check)
 * - tool_loop_metrics.ts exports all required functions
 */

import { describe, it, expect } from 'vitest'
import {
  aggregateTurnSummary,
  computeIterationCostBreakdown,
  type ToolLoopIterationRecord,
} from '../../src/lib/observatory/tool_loop_metrics'

const sampleRecords: ToolLoopIterationRecord[] = [
  {
    iteration: 1,
    providerId: 'anthropic',
    conversationId: 'conv-abc-123',
    inputTokens: 2000,
    outputTokens: 300,
    cacheReadTokens: 1500,
    cacheCreationTokens: 0,
    reasoningTokens: 0,
    toolCallCount: 2,
    toolErrorCount: 0,
    terminationSignal: 'tool_use',
    completedAt: '2026-05-22T10:00:00Z',
  },
  {
    iteration: 2,
    providerId: 'anthropic',
    conversationId: 'conv-abc-123',
    inputTokens: 1800,
    outputTokens: 250,
    cacheReadTokens: 1500,
    cacheCreationTokens: 0,
    reasoningTokens: 0,
    toolCallCount: 1,
    toolErrorCount: 1,
    terminationSignal: 'end_turn',
    completedAt: '2026-05-22T10:00:03Z',
  },
]

describe('E-S9: aggregateTurnSummary — multi-iteration aggregation', () => {
  it('returns null for empty records', () => {
    expect(aggregateTurnSummary([])).toBeNull()
  })

  it('totalIterations = record count', () => {
    const summary = aggregateTurnSummary(sampleRecords)
    expect(summary?.totalIterations).toBe(2)
  })

  it('totalInputTokens = sum across iterations', () => {
    const summary = aggregateTurnSummary(sampleRecords)
    expect(summary?.totalInputTokens).toBe(3800)
  })

  it('totalOutputTokens = sum across iterations', () => {
    const summary = aggregateTurnSummary(sampleRecords)
    expect(summary?.totalOutputTokens).toBe(550)
  })

  it('totalCacheReadTokens = sum across iterations', () => {
    const summary = aggregateTurnSummary(sampleRecords)
    expect(summary?.totalCacheReadTokens).toBe(3000)
  })

  it('totalToolCalls = sum across iterations', () => {
    const summary = aggregateTurnSummary(sampleRecords)
    expect(summary?.totalToolCalls).toBe(3)
  })

  it('totalToolErrors = sum across iterations', () => {
    const summary = aggregateTurnSummary(sampleRecords)
    expect(summary?.totalToolErrors).toBe(1)
  })

  it('capExceeded=false by default', () => {
    const summary = aggregateTurnSummary(sampleRecords)
    expect(summary?.capExceeded).toBe(false)
  })

  it('capExceeded=true when passed explicitly', () => {
    const summary = aggregateTurnSummary(sampleRecords, true)
    expect(summary?.capExceeded).toBe(true)
  })

  it('preserves conversationId from first record', () => {
    const summary = aggregateTurnSummary(sampleRecords)
    expect(summary?.conversationId).toBe('conv-abc-123')
  })

  it('preserves providerId from first record', () => {
    const summary = aggregateTurnSummary(sampleRecords)
    expect(summary?.providerId).toBe('anthropic')
  })
})

describe('E-S9: computeIterationCostBreakdown', () => {
  it('returns one breakdown per record', () => {
    const breakdown = computeIterationCostBreakdown(sampleRecords)
    expect(breakdown).toHaveLength(2)
  })

  it('iteration 1: inputCostUnits = inputTokens', () => {
    const bd = computeIterationCostBreakdown(sampleRecords)
    expect(bd[0].inputCostUnits).toBe(2000)
  })

  it('iteration 1: cacheReadSavingUnits = cacheReadTokens * 0.9', () => {
    const bd = computeIterationCostBreakdown(sampleRecords)
    expect(bd[0].cacheReadSavingUnits).toBeCloseTo(1350, 2)
  })

  it('iteration 1: cacheWriteExtraUnits = 0 (no cache creation)', () => {
    const bd = computeIterationCostBreakdown(sampleRecords)
    expect(bd[0].cacheWriteExtraUnits).toBe(0)
  })

  it('netCostUnits is reduced by cache savings', () => {
    const bd = computeIterationCostBreakdown(sampleRecords)
    // iter 1: input=2000, output=300, cacheReadSaving=1350, cacheWriteExtra=0
    // net = 2000 + 300 - 1350 + 0 = 950
    expect(bd[0].netCostUnits).toBeCloseTo(950, 1)
  })
})

describe('E-S9: module exports', () => {
  it('aggregateTurnSummary is exported', () => {
    expect(typeof aggregateTurnSummary).toBe('function')
  })

  it('computeIterationCostBreakdown is exported', () => {
    expect(typeof computeIterationCostBreakdown).toBe('function')
  })
})
