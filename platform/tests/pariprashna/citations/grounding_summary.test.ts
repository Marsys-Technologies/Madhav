/**
 * G2-B "Citations at first paint" (PPR-08, FD-2/FD-6) —
 * `buildGroundingSummary`.
 *
 * Real assertions against constructed inputs (§N.8 — not a tautology): every
 * number this test checks is independently computed by hand from the fixture
 * input, then compared against the function's output.
 */

import { describe, it, expect } from 'vitest'
import { buildGroundingSummary } from '@/lib/pariprashna/citations/grounding_summary'
import type { ResolvedTurnCitation } from '@/lib/pariprashna/citations/stream_wiring'
import type { WebCompletenessReceipt } from '@/lib/pipeline/completeness_wiring'

function citation(overrides: Partial<ResolvedTurnCitation>): ResolvedTurnCitation {
  return {
    index: 1,
    signal_id: 'SIG.MSR.001',
    layer: 'L2.5',
    snippet: 'a snippet',
    grade: 'primary',
    ...overrides,
  }
}

describe('buildGroundingSummary', () => {
  it('tallies grade_counts to match the exact input distribution', () => {
    const resolvedCitations: ResolvedTurnCitation[] = [
      citation({ index: 1, signal_id: 'SIG.MSR.001', grade: 'primary' }),
      citation({ index: 2, signal_id: 'SIG.MSR.002', grade: 'primary' }),
      citation({ index: 3, signal_id: 'SIG.MSR.003', grade: 'supporting' }),
      citation({ index: 4, signal_id: 'SIG.MSR.004', grade: 'contextual' }),
      citation({ index: 5, signal_id: 'SIG.MSR.005', grade: 'unverified' }),
      citation({ index: 6, signal_id: 'SIG.MSR.006', grade: 'prior_reading' }),
    ]
    const summary = buildGroundingSummary({
      resolvedCitations,
      hallucinationCount: 1,
      completenessReceipt: null,
    })

    // Hand-counted against the fixture above — not derived from the same code path.
    expect(summary.citation_count).toBe(6)
    expect(summary.hallucination_count).toBe(1)
    expect(summary.grade_counts).toEqual({
      primary: 2,
      supporting: 1,
      contextual: 1,
      unverified: 1,
      prior_reading: 1,
    })
    expect(summary.completeness).toBeNull()
    expect(summary.completeness_line).toBeNull()
  })

  it('restates (never recomputes) the completeness receipt coverage numbers', () => {
    const receipt = {
      coverage: { floor_item_total: 6, served: 4, empty: 1, dark: 1 },
      channel_note: 'n/a',
    } as unknown as WebCompletenessReceipt

    const summary = buildGroundingSummary({
      resolvedCitations: [],
      hallucinationCount: 0,
      completenessReceipt: receipt,
    })

    expect(summary.citation_count).toBe(0)
    expect(summary.completeness).toEqual({ served: 4, floor_item_total: 6 })
    expect(summary.completeness_line).toBe('4/6 floor items served')
  })

  it('an empty turn (no citations, no receipt) is an honest all-zero/null summary', () => {
    const summary = buildGroundingSummary({
      resolvedCitations: [],
      hallucinationCount: 0,
      completenessReceipt: null,
    })
    expect(summary.citation_count).toBe(0)
    expect(summary.grade_counts).toEqual({
      primary: 0,
      supporting: 0,
      contextual: 0,
      unverified: 0,
      prior_reading: 0,
    })
    expect(summary.completeness).toBeNull()
    expect(summary.completeness_line).toBeNull()
  })
})
