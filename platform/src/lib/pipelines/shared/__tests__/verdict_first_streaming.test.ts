/**
 * Tests for W5 Lane L9 — verdict-first streaming.
 *
 * `buildFirstVerdictEmission` (run_adapter_dispatch.ts) is the pure builder that decides what the
 * adapter-dispatch stream writes FIRST, before any synthesis text-delta: the `data-orientation`
 * verdict/orientation layer, plus a `data-stage` (`first_verdict`) sample of the time-to-first-
 * verdict SLO metric (STATE.md W5 OPEN amendment 3; TIME_TO_FIRST_VERDICT_SLO_MS in
 * @/lib/streams/data_parts). Kept pure (no Date.now(), no I/O) so this suite can assert exact
 * elapsed-ms values deterministically instead of just checking an event fires.
 */

import { describe, it, expect } from 'vitest'
import { buildFirstVerdictEmission } from '../run_adapter_dispatch'
import { StagePartSchema, OrientationPartSchema, TIME_TO_FIRST_VERDICT_SLO_MS } from '@/lib/streams/data_parts'
import type { ChartOrientation } from '@/lib/retrieval/orientation'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

function fakeOrientation(overrides: Partial<ChartOrientation> = {}): ChartOrientation {
  return {
    chart_id: CHART_ID,
    ayanamsha_id: 'lahiri',
    chart_header: null,
    header_flags: [],
    structural_facts: {
      msr_signal_count: 12,
      yoga_count: 3,
      dosha_count: 1,
      contradiction_count: 0,
      weakest_graha: 'Jupiter',
      weakest_graha_source: 'shadbala',
      top_priority_class: 'career',
    },
    notable_findings: [],
    convergence_domains: [],
    dasha_context: { current_maha_antar: 'Saturn/Mercury' },
    category_inventory: [],
    budget: { limit_tokens: 2000, estimated_tokens: 400, enforced: false, trims: [] },
    degraded: false,
    ...overrides,
  }
}

describe('buildFirstVerdictEmission — time-to-first-verdict stage timing', () => {
  it('computes ms as the exact elapsed time between requestStartedAt and nowMs', () => {
    const requestStartedAt = 1_000_000
    const nowMs = 1_000_000 + 4_600 + 50 + 6_100 // classify + compose_bundle + tool_fetch, W4 baseline
    const result = buildFirstVerdictEmission(fakeOrientation(), CHART_ID, requestStartedAt, nowMs)

    expect(result.timeToFirstVerdictMs).toBe(10_750)
    expect(result.stageEvent.data.stage).toBe('first_verdict')
    expect(result.stageEvent.data.status).toBe('done')
    expect(result.stageEvent.data.ms).toBe(10_750)
  })

  it('never returns a negative ms even if nowMs somehow precedes requestStartedAt', () => {
    const result = buildFirstVerdictEmission(fakeOrientation(), CHART_ID, 2_000, 1_000)
    expect(result.timeToFirstVerdictMs).toBe(0)
    expect(result.stageEvent.data.ms).toBe(0)
  })

  it('the W4-measured pre-synthesis baseline (10.75s) sits comfortably under the p50 SLO target', () => {
    // classify 4.6s + compose_bundle 0.05s + tool_fetch 6.1s (measured at W4 close, chart
    // 1c826d5a) — the pre-synthesis stage sum the first_verdict write follows immediately.
    const measuredPreSynthesisMs = 4_600 + 50 + 6_100
    expect(measuredPreSynthesisMs).toBeLessThan(TIME_TO_FIRST_VERDICT_SLO_MS.p50)
    // And nowhere close to the 38.7s synthesis stage alone, let alone the ~51s total.
    expect(TIME_TO_FIRST_VERDICT_SLO_MS.p95).toBeLessThan(38_700)
  })

  it('produces a schema-valid data-stage payload', () => {
    const result = buildFirstVerdictEmission(fakeOrientation(), CHART_ID, 0, 12_000)
    expect(StagePartSchema.safeParse(result.stageEvent.data).success).toBe(true)
  })
})

describe('buildFirstVerdictEmission — verdict-first coverage (100% of dispatched query classes)', () => {
  it('emits a real orientation payload when buildChartOrientation succeeded', () => {
    const result = buildFirstVerdictEmission(fakeOrientation(), CHART_ID, 0, 100)
    expect(result.orientationEvent.type).toBe('data-orientation')
    expect(result.orientationEvent.data.degraded).toBe(false)
    expect(result.orientationEvent.data.chart_id).toBe(CHART_ID)
    expect(OrientationPartSchema.safeParse(result.orientationEvent.data).success).toBe(true)
  })

  it('CLOSES THE GAP: still emits a degraded orientation + first_verdict stage sample when orientation is null (outright build failure)', () => {
    const result = buildFirstVerdictEmission(null, CHART_ID, 0, 500)

    // Previously (pre-W5-L9): `if (orientation) { writer.write(...) }` meant a hard
    // buildChartOrientation failure silently dropped the data-orientation event entirely for
    // that request — a verdict-first coverage gap. Now a degraded fallback is always emitted.
    expect(result.orientationEvent.type).toBe('data-orientation')
    expect(result.orientationEvent.data.degraded).toBe(true)
    expect(result.orientationEvent.data.chart_id).toBe(CHART_ID)
    expect(OrientationPartSchema.safeParse(result.orientationEvent.data).success).toBe(true)

    // The time-to-first-verdict SLO sample still fires — coverage is unconditional, not
    // contingent on the orientation build having succeeded.
    expect(result.stageEvent.data.stage).toBe('first_verdict')
    expect(result.timeToFirstVerdictMs).toBe(500)
  })

  it('CLOSES THE GAP: same guarantee when orientation is undefined', () => {
    const result = buildFirstVerdictEmission(undefined, CHART_ID, 1_000, 1_300)
    expect(result.orientationEvent.data.degraded).toBe(true)
    expect(result.timeToFirstVerdictMs).toBe(300)
  })

  it('degraded fallback never fabricates structural facts or notable findings', () => {
    const result = buildFirstVerdictEmission(null, CHART_ID, 0, 0)
    const payload = result.orientationEvent.data.orientation as Record<string, unknown>
    expect(payload['header_flags']).toEqual(['orientation_build_unavailable'])
    // No structural_facts / notable_findings key fabricated on the degraded passthrough object —
    // absent, not falsely populated (B.10 — no fabricated computation).
    expect(payload['structural_facts']).toBeUndefined()
    expect(payload['notable_findings']).toBeUndefined()
  })
})
