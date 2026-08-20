/**
 * observability/interpretation_metrics.test.ts — lane G3-B (PPR-02).
 *
 * `computeInterpretationSetsMetrics` is the REAL measured waiver rate —
 * proves it is computed from the actual entries array (never hardcoded),
 * including the honest `null` rate when nothing was covered this turn.
 */
import { describe, it, expect } from 'vitest'

import { computeInterpretationSetsMetrics } from '../interpretation_metrics'

describe('computeInterpretationSetsMetrics', () => {
  it('computes a real, non-zero waiver rate from a mixed set', () => {
    const metrics = computeInterpretationSetsMetrics([
      { status: 'generated' },
      { status: 'generated' },
      { status: 'waived' },
    ])
    expect(metrics.covered_count).toBe(3)
    expect(metrics.generated_count).toBe(2)
    expect(metrics.waived_count).toBe(1)
    expect(metrics.waiver_rate).toBeCloseTo(1 / 3)
  })

  it('is 0 (a real measured zero), not merely absent, when nothing was waived', () => {
    const metrics = computeInterpretationSetsMetrics([{ status: 'generated' }, { status: 'generated' }])
    expect(metrics.waived_count).toBe(0)
    expect(metrics.waiver_rate).toBe(0)
  })

  it('is 1 (a real measured one) when every judgment was waived', () => {
    const metrics = computeInterpretationSetsMetrics([{ status: 'waived' }])
    expect(metrics.waiver_rate).toBe(1)
  })

  it('reports an HONEST null rate — not a fabricated 0 — when nothing was covered', () => {
    const metrics = computeInterpretationSetsMetrics([])
    expect(metrics.covered_count).toBe(0)
    expect(metrics.waiver_rate).toBeNull()
  })
})
