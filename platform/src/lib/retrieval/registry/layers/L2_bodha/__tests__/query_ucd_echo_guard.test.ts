/**
 * WP-0.1 / LCA-17 — query_ucd chart_id echo-back guard (defense-in-depth).
 *
 * These pure helpers back the server-side assertion that query_ucd never serves a
 * payload (cached or fresh) whose echoed chart identity differs from the requested
 * chart_id — the cross-chart substitution class (F-0893/0902/0905/0908).
 */

import { describe, it, expect } from 'vitest'
import { orientationChartIdOf, orientationEchoMatches } from '../query_ucd'

const CHART_A = 'eaf4b85b-9549-4838-9439-3fab4b11572e'
const CHART_B = '4b9bba4b-67ef-4c11-a4fe-05299f30780e'

describe('WP-0.1 / LCA-17 — orientation echo-back guard', () => {
  it('extracts the echoed chart_id from a well-formed payload', () => {
    const payload = { content: { chart_id: CHART_A, digest: {} }, is_error: false }
    expect(orientationChartIdOf(payload)).toBe(CHART_A)
  })

  it('returns undefined when no chart identity is present (never trusted)', () => {
    expect(orientationChartIdOf(undefined)).toBeUndefined()
    expect(orientationChartIdOf(null)).toBeUndefined()
    expect(orientationChartIdOf({})).toBeUndefined()
    expect(orientationChartIdOf({ content: {} })).toBeUndefined()
    expect(orientationChartIdOf({ content: { chart_id: 42 } })).toBeUndefined()
  })

  it('matches only when the echoed chart_id equals the requested chart_id', () => {
    const payloadForA = { content: { chart_id: CHART_A } }
    expect(orientationEchoMatches(payloadForA, CHART_A)).toBe(true)
    // The exact substitution: a chart-A payload served for a chart-B request.
    expect(orientationEchoMatches(payloadForA, CHART_B)).toBe(false)
  })

  it('treats an unreadable payload as a non-match (fail-closed)', () => {
    expect(orientationEchoMatches({}, CHART_A)).toBe(false)
    expect(orientationEchoMatches(undefined, CHART_A)).toBe(false)
  })
})
